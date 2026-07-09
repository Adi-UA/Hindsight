"""Tests for the Trader order flow, using mocked Alpaca clients."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from alpaca.trading.enums import OrderSide

from strategy import Signal


def test_run_once_buy_uses_buy_fraction(make_trader):
    trader, trade_client = make_trader(signal=Signal.BUY, cash=1000.0)
    decision = trader.run_once()
    assert decision.action == "BUY"
    assert decision.amount == 750.0  # 1000 * default buy_fraction 0.75
    assert decision.status == "FILLED"
    trade_client.submit_order.assert_called_once()


def test_run_once_sell_uses_sell_fraction(make_trader):
    position = SimpleNamespace(symbol="VOO", qty="10", market_value="1000")
    trader, trade_client = make_trader(signal=Signal.SELL, positions=[position])
    decision = trader.run_once()
    assert decision.action == "SELL"
    assert decision.amount == 1.0  # 10 * default sell_fraction 0.10
    assert decision.status == "FILLED"


def test_run_once_hold_places_no_order(make_trader):
    trader, trade_client = make_trader(signal=Signal.HOLD)
    decision = trader.run_once()
    assert decision.action == "NONE"
    assert decision.status == "NONE"
    trade_client.submit_order.assert_not_called()


def test_run_once_sell_without_position_is_noop(make_trader):
    trader, trade_client = make_trader(signal=Signal.SELL, positions=[])
    decision = trader.run_once()
    assert decision.action == "NONE"
    trade_client.submit_order.assert_not_called()


def test_unfilled_order_is_cancelled(make_trader):
    trader, trade_client = make_trader(signal=Signal.BUY, order_status="new")
    decision = trader.run_once()
    assert decision.status == "CANCELLED"
    trade_client.cancel_order_by_id.assert_called_once()


def test_place_order_requires_amount(make_trader):
    trader, _ = make_trader()
    with pytest.raises(ValueError):
        trader._place_order(side=OrderSide.BUY)


def test_fetch_closing_prices_are_sorted(make_trader):
    trader, _ = make_trader()
    bars = SimpleNamespace(
        data={
            "VOO": [
                SimpleNamespace(timestamp=2, close=11.0),
                SimpleNamespace(timestamp=1, close=10.0),
            ]
        }
    )
    assert trader._fetch_stock_closing_prices(bars) == [10.0, 11.0]


def test_account_snapshot_reports_position(make_trader):
    position = SimpleNamespace(symbol="VOO", qty="5", market_value="500")
    trader, _ = make_trader(positions=[position])
    snapshot = trader.account_snapshot()
    assert snapshot["cash"] == 1000.0
    assert snapshot["position_qty"] == 5.0
    assert snapshot["position_value"] == 500.0


def test_invalid_fractions_are_rejected(make_trader, monkeypatch):
    # buy_fraction outside (0, 1] must raise before any client call.
    from conftest import StubStrategy
    from trader import Trader

    monkeypatch.setattr("trader.TradingClient", lambda **kw: None)
    monkeypatch.setattr("trader.StockHistoricalDataClient", lambda **kw: None)
    with pytest.raises(ValueError):
        Trader(strategy=StubStrategy(), buy_fraction=1.5)
