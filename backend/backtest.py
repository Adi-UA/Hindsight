"""Headless backtesting that returns data for charting (no plot window).

Fetches historical daily bars once and runs one or more strategies over the
same data with backtrader, returning JSON-friendly metrics plus per-bar series
(close price and portfolio equity) so a frontend can draw and compare them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import backtrader as bt
import pandas as pd
import yfinance as yf

from pricecache import PriceCache, RateLimitError
from strategy import STRATEGIES, Signal, Strategy, get_strategy

# Per-process cache + fetch limiter shared across requests.
_PRICE_CACHE = PriceCache()

# Full-invest benchmarks deploy nearly all cash at once; leave a small buffer
# so the order still fills if the next open ticks up.
_FULL_INVEST_FRACTION = 0.99


class _StrategyBridge(bt.Strategy):
    """Adapts a SimpleTrader :class:`Strategy` to a backtrader strategy."""

    params = dict(  # noqa: RUF012 - backtrader reads params from a dict/tuple
        strategy_obj=None,
        buy_fraction=0.75,
        sell_fraction=0.10,
        interval_days=2,
        lookback=60,
    )

    def __init__(self) -> None:
        self.dataclose = self.datas[0].close
        self.equity_curve: list[tuple[str, float, float]] = []
        self.markers: list[tuple[str, str, float]] = []
        self._last_trade_date = None

    def next(self) -> None:
        current_date = self.datas[0].datetime.date(0)
        price = float(self.dataclose[0])
        self.equity_curve.append(
            (current_date.isoformat(), price, float(self.broker.getvalue()))
        )

        if (
            self._last_trade_date is not None
            and (current_date - self._last_trade_date).days < self.p.interval_days
        ):
            return

        strategy: Strategy = self.p.strategy_obj
        closes = list(self.dataclose.get(size=self.p.lookback))
        if len(closes) < strategy.min_bars:
            return

        signal = strategy.decide(closes)
        if signal is Signal.BUY:
            if strategy.full_invest:
                # Buy & hold: target a fixed share of the portfolio once, then
                # hold. order_target_percent sizes correctly at execution.
                if self.position.size > 0:
                    return
                self.order_target_percent(target=_FULL_INVEST_FRACTION)
                self.markers.append((current_date.isoformat(), "BUY", price))
                self._last_trade_date = current_date
            else:
                size = self.broker.get_cash() * self.p.buy_fraction / price
                if size > 0:
                    self.buy(size=size)
                    self.markers.append((current_date.isoformat(), "BUY", price))
                    self._last_trade_date = current_date
        elif signal is Signal.SELL and self.position.size > 0:
            size = self.position.size * self.p.sell_fraction
            self.sell(size=size)
            self.markers.append((current_date.isoformat(), "SELL", price))
            self._last_trade_date = current_date


def _feed_from_df(df: pd.DataFrame) -> bt.feeds.PandasData:
    """Build a backtrader feed from an OHLCV DataFrame (datetime index)."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return bt.feeds.PandasData(
        dataname=df,
        open="Open",
        high="High",
        low="Low",
        close="Close",
        volume="Volume",
        openinterest=None,
    )


def _load_yf_df(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Download OHLCV data for a symbol; raise if none is available.

    Results are cached per-process; cache misses are rate limited to avoid
    hammering Yahoo Finance.
    """
    key = _PRICE_CACHE.key(symbol, start, end)
    cached = _PRICE_CACHE.get(key)
    if cached is not None:
        return cached

    if not _PRICE_CACHE.allow_fetch():
        raise RateLimitError("Too many data requests right now. Please try again shortly.")

    df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"No price data for {symbol} between {start} and {end}")
    _PRICE_CACHE.put(key, df)
    return df


def _max_drawdown_pct(equities: list[float]) -> float:
    peak = float("-inf")
    max_dd = 0.0
    for value in equities:
        peak = max(peak, value)
        if peak > 0:
            max_dd = max(max_dd, (peak - value) / peak)
    return round(max_dd * 100, 2)


def _to_iso(value: str | datetime) -> str:
    return value.date().isoformat() if isinstance(value, datetime) else str(value)


def _run_one(
    strategy: Strategy,
    feed: bt.feeds.PandasData,
    cash: float,
    buy_fraction: float = 0.75,
    sell_fraction: float = 0.10,
    interval_days: int = 2,
) -> dict[str, Any]:
    """Run a single strategy over a prepared feed and return its result."""
    cerebro = bt.Cerebro()
    # Only wait for as much history as the strategy actually needs, so it starts
    # as early as it validly can (buy & hold enters almost immediately).
    lookback = strategy.min_bars
    cerebro.addstrategy(
        _StrategyBridge,
        strategy_obj=strategy,
        buy_fraction=buy_fraction,
        sell_fraction=sell_fraction,
        interval_days=interval_days,
        lookback=lookback,
    )
    cerebro.broker.set_cash(cash)
    cerebro.adddata(feed)

    result = cerebro.run()[0]
    final_value = float(cerebro.broker.getvalue())
    equities = [equity for _, _, equity in result.equity_curve]

    return {
        "strategy": strategy.name,
        "final_value": round(final_value, 2),
        "return_pct": round((final_value / cash - 1) * 100, 2) if cash else 0.0,
        "num_trades": len(result.markers),
        "max_drawdown_pct": _max_drawdown_pct(equities),
        "series": [
            {"date": d, "close": c, "equity": e} for d, c, e in result.equity_curve
        ],
        "markers": [{"date": d, "side": s, "price": p} for d, s, p in result.markers],
    }


def run_backtest(
    strategy: Strategy,
    symbol: str,
    start: str | datetime,
    end: str | datetime,
    cash: float = 10_000.0,
    buy_fraction: float = 0.75,
    sell_fraction: float = 0.10,
    interval_days: int = 2,
    data: bt.feeds.PandasData | None = None,
) -> dict[str, Any]:
    """Run one strategy and return its metrics + series (with symbol/date meta)."""
    feed = data if data is not None else _feed_from_df(_load_yf_df(symbol, str(start), str(end)))
    result = _run_one(strategy, feed, cash, buy_fraction, sell_fraction, interval_days)
    return {
        "symbol": symbol,
        "start": _to_iso(start),
        "end": _to_iso(end),
        "initial_cash": round(cash, 2),
        **result,
    }


def run_comparison(
    strategies: list[Strategy],
    symbol: str,
    start: str | datetime,
    end: str | datetime,
    cash: float = 10_000.0,
    buy_fraction: float = 0.75,
    sell_fraction: float = 0.10,
    interval_days: int = 2,
    df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Run several strategies over the SAME data (fetched once) and compare them."""
    frame = df if df is not None else _load_yf_df(symbol, str(start), str(end))
    results = [
        _run_one(s, _feed_from_df(frame.copy()), cash, buy_fraction, sell_fraction, interval_days)
        for s in strategies
    ]
    return {
        "symbol": symbol,
        "start": _to_iso(start),
        "end": _to_iso(end),
        "initial_cash": round(cash, 2),
        "results": results,
    }


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Backtest one or more SimpleTrader strategies on historical data."
    )
    parser.add_argument("--symbol", required=True, help="Ticker symbol, e.g. VOO")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    parser.add_argument(
        "--strategies",
        default="sma_crossover",
        help=f"Comma-separated strategies from: {', '.join(STRATEGIES)}",
    )
    parser.add_argument("--cash", type=float, default=10_000.0, help="Starting cash")
    args = parser.parse_args()

    names = [n.strip() for n in args.strategies.split(",") if n.strip()]
    strategies = [get_strategy(n) for n in names]
    result = run_comparison(strategies, args.symbol, args.start, args.end, cash=args.cash)
    summary = {
        "symbol": result["symbol"],
        "start": result["start"],
        "end": result["end"],
        "initial_cash": result["initial_cash"],
        "results": [
            {k: v for k, v in r.items() if k not in ("series", "markers")}
            for r in result["results"]
        ],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
