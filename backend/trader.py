"""The core trader: turns a strategy signal into a sized Alpaca order.

The :class:`Trader` owns the brokerage connection and the mechanics of trading
(account validation, order placement, fill monitoring, decision logging). It
delegates *what* to do to a :class:`~strategy.Strategy` and only decides *how
much* to trade via the configured buy/sell fractions. Scheduling lives in
:class:`~bot_runner.BotRunner`, not here, so a single call to :meth:`run_once`
performs exactly one decision-and-trade cycle and is easy to test.
"""

from __future__ import annotations

import logging
import os
import time as systime
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from strategy import Signal, Strategy

NY_TZ = ZoneInfo("America/New_York")
_TRADE_LOG = "logs/decisions.csv"


@dataclass
class Decision:
    """A single record of what the bot decided (and did) on one run."""

    timestamp: str
    symbol: str
    strategy: str
    signal: str
    action: str  # BUY, SELL or NONE
    amount: float | None
    status: str  # FILLED, CANCELLED or NONE

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class Trader:
    """Manage an automated trading strategy against the Alpaca API.

    Args:
        strategy: The decision-making strategy to run.
        symbol: Ticker to trade.
        api_key: Alpaca API key.
        secret_key: Alpaca secret key.
        paper: Use the paper trading endpoint. Pair with paper keys.
        buy_fraction: Fraction of available cash to deploy on a BUY.
        sell_fraction: Fraction of the current position to sell on a SELL.
        max_wait: Seconds to wait for an order to fill before cancelling.
        debug: Enable debug logging.
    """

    def __init__(
        self,
        strategy: Strategy,
        symbol: str = "VOO",
        api_key: str | None = None,
        secret_key: str | None = None,
        paper: bool = True,
        buy_fraction: float = 0.75,
        sell_fraction: float = 0.10,
        max_wait: int = 300,
        debug: bool = False,
    ) -> None:
        if not 0 < buy_fraction <= 1:
            raise ValueError("buy_fraction must be in (0, 1]")
        if not 0 < sell_fraction <= 1:
            raise ValueError("sell_fraction must be in (0, 1]")

        self._init_logging(debug)
        self.strategy = strategy
        self.symbol = symbol
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self.buy_fraction = buy_fraction
        self.sell_fraction = sell_fraction
        self.max_wait = max_wait
        self.tz = NY_TZ

        self.trade_client = self._get_trading_client()
        self.stock_historical_data_client = self._get_stock_historical_data_client()

    def _init_logging(self, debug: bool) -> None:
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    # --- client setup --------------------------------------------------------

    def _validate_account(self, trade_client: TradingClient) -> tuple[bool, str | None]:
        """Check the account is active, funded and configured for fractional trades."""
        logging.info("Validating account...")
        account = trade_client.get_account()
        configurations = trade_client.get_account_configurations()
        logging.debug(f"Account information: {account}")

        errors = []
        if account.status != "ACTIVE":
            errors.append("Account is not active. Please check your account status.")
        if not configurations.fractional_trading:
            errors.append("Fractional trading is not enabled. Please enable it.")
        if float(account.cash) < 0:
            errors.append("Balance is negative. Please deposit funds to continue trading.")

        if errors:
            error_message = "\n".join([f"- {err}" for err in errors])
            logging.error(f"Account validation failed:\n{error_message}")
            return False, error_message

        logging.info("Account validated successfully.")
        return True, None

    def _get_trading_client(self) -> TradingClient:
        trade_client = TradingClient(
            api_key=self.api_key, secret_key=self.secret_key, paper=self.paper
        )
        is_valid, error = self._validate_account(trade_client)
        if not is_valid:
            raise RuntimeError(error)
        return trade_client

    def _get_stock_historical_data_client(self) -> StockHistoricalDataClient:
        return StockHistoricalDataClient(api_key=self.api_key, secret_key=self.secret_key)

    # --- market data ---------------------------------------------------------

    def _fetch_stock_bars(
        self,
        start_date: datetime,
        end_date: datetime,
        timeframe: TimeFrame,
        limit: int | None = None,
    ):
        """Fetch historical bars for the configured symbol."""
        request = StockBarsRequest(
            symbol_or_symbols=self.symbol,
            start=start_date,
            end=end_date,
            timeframe=timeframe,
            limit=limit,
        )
        bars = self.stock_historical_data_client.get_stock_bars(request)
        logging.debug(f"Fetched bars for {self.symbol} from {start_date} to {end_date}")
        return bars

    def _fetch_stock_closing_prices(self, bars) -> list[float]:
        """Extract closing prices in chronological order (oldest first)."""
        data = bars.data[self.symbol]
        pairs = sorted(((bar.timestamp, bar.close) for bar in data), key=lambda x: x[0])
        closing_prices = [price for _, price in pairs]
        logging.debug(f"Closing prices: {closing_prices}")
        return closing_prices

    def _recent_closes(self, count: int) -> list[float]:
        """Return the most recent ``count`` daily closes (oldest first)."""
        now = datetime.now(self.tz)
        # Reach back well past `count` trading days to cover weekends/holidays,
        # then keep only the most recent `count` closes.
        bars = self._fetch_stock_bars(
            start_date=now - timedelta(days=count * 2 + 15),
            end_date=now - timedelta(days=1),
            timeframe=TimeFrame.Day,
        )
        return self._fetch_stock_closing_prices(bars)[-count:]

    # --- order placement -----------------------------------------------------

    def _place_order(
        self,
        qty: float | None = None,
        notional: float | None = None,
        side: OrderSide | None = None,
    ) -> bool:
        """Submit a market order and wait for it to fill (or time out)."""
        order_type = "NOTIONAL" if notional else "FRACTIONAL"
        request_params: dict[str, object] = {
            "symbol": self.symbol,
            "side": side,
            "type": OrderType.MARKET,
            "time_in_force": TimeInForce.DAY,
        }
        if notional:
            request_params["notional"] = notional
        elif qty:
            request_params["qty"] = qty
        else:
            raise ValueError("Either 'qty' or 'notional' must be provided.")

        request = MarketOrderRequest(**request_params)
        order = self.trade_client.submit_order(request)
        logging.info(f"Order placed: {order}")
        return self._monitor_order(order, qty or notional, order_type, side)

    def _monitor_order(self, order, amount, trade_type, side) -> bool:
        """Poll an order until it fills or the wait budget runs out."""
        logging.info("Monitoring order status...")
        remaining_time = self.max_wait
        wait_step = 60
        while order.status != "filled" and remaining_time > 0:
            systime.sleep(wait_step)
            remaining_time -= wait_step
            order = self.trade_client.get_order_by_id(order.id)
            logging.info(f"Order status: {order.status}")

        filled = order.status == "filled"
        if not filled:
            self.trade_client.cancel_order_by_id(order.id)
        logging.info(f"Final order status: {'FILLED' if filled else 'CANCELLED'}")
        return filled

    def _current_position(self):
        """Return the open position for the symbol, or None."""
        positions = self.trade_client.get_all_positions()
        for pos in positions:
            if pos.symbol == self.symbol:
                return pos
        return None

    def _log_decision(self, decision: Decision) -> None:
        """Append the decision to the CSV decision log."""
        os.makedirs(os.path.dirname(_TRADE_LOG) or ".", exist_ok=True)
        new_file = not os.path.exists(_TRADE_LOG)
        with open(_TRADE_LOG, "a", encoding="utf-8") as f:
            if new_file:
                f.write("timestamp,symbol,strategy,signal,action,amount,status\n")
            f.write(
                f"{decision.timestamp},{decision.symbol},{decision.strategy},"
                f"{decision.signal},{decision.action},{decision.amount},{decision.status}\n"
            )

    # --- one decision cycle --------------------------------------------------

    def run_once(self) -> Decision:
        """Fetch data, ask the strategy for a signal, and act on it once."""
        closes = self._recent_closes(self.strategy.min_bars)
        signal = self.strategy.decide(closes)
        logging.info(f"Strategy {self.strategy.name} -> {signal.value}")

        action, amount, status = "NONE", None, "NONE"

        if signal is Signal.BUY:
            cash = float(self.trade_client.get_account().cash)
            notional = round(cash * self.buy_fraction, 2)
            if notional > 0:
                filled = self._place_order(notional=notional, side=OrderSide.BUY)
                action, amount = "BUY", notional
                status = "FILLED" if filled else "CANCELLED"
        elif signal is Signal.SELL:
            position = self._current_position()
            if position is not None:
                qty = float(position.qty) * self.sell_fraction
                if qty > 0:
                    filled = self._place_order(qty=qty, side=OrderSide.SELL)
                    action, amount = "SELL", qty
                    status = "FILLED" if filled else "CANCELLED"

        decision = Decision(
            timestamp=datetime.now(self.tz).isoformat(timespec="seconds"),
            symbol=self.symbol,
            strategy=self.strategy.name,
            signal=signal.value,
            action=action,
            amount=amount,
            status=status,
        )
        self._log_decision(decision)
        return decision

    def account_snapshot(self) -> dict[str, object]:
        """Return a small account summary for the dashboard status card."""
        account = self.trade_client.get_account()
        position = self._current_position()
        return {
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "position_qty": float(position.qty) if position else 0.0,
            "position_value": float(position.market_value) if position else 0.0,
        }
