"""Shared pytest fixtures: a mock-backed Trader and an API test client."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from strategy import Signal, Strategy
from trader import Trader


class StubStrategy(Strategy):
    """A strategy that returns a fixed signal, for deterministic trader tests."""

    name = "stub"
    description = "stub strategy for tests"

    def __init__(self, signal: Signal = Signal.HOLD, min_bars: int = 5) -> None:
        self._signal = signal
        self._min_bars = min_bars

    @property
    def min_bars(self) -> int:
        return self._min_bars

    def decide(self, closes):  # noqa: ANN001 - test stub
        return self._signal


@pytest.fixture
def make_trader(monkeypatch, tmp_path):
    """Build a Trader whose Alpaca clients are mocked (no network, no keys)."""

    def _make(signal=Signal.HOLD, cash=1000.0, positions=None, order_status="filled"):
        order = SimpleNamespace(id="order-1", status=order_status)
        trade_client = MagicMock()
        trade_client.get_account.return_value = SimpleNamespace(
            status="ACTIVE", cash=str(cash), portfolio_value=str(cash)
        )
        trade_client.get_account_configurations.return_value = SimpleNamespace(
            fractional_trading=True
        )
        trade_client.get_all_positions.return_value = positions or []
        trade_client.submit_order.return_value = order
        trade_client.get_order_by_id.return_value = order

        monkeypatch.setattr("trader.TradingClient", lambda **kw: trade_client)
        monkeypatch.setattr("trader.StockHistoricalDataClient", lambda **kw: MagicMock())
        monkeypatch.setattr("trader.systime.sleep", lambda *a, **k: None)
        monkeypatch.setattr("trader._TRADE_LOG", str(tmp_path / "decisions.csv"))

        trader = Trader(
            strategy=StubStrategy(signal),
            symbol="VOO",
            api_key="k",
            secret_key="s",
            paper=True,
        )
        monkeypatch.setattr(trader, "_recent_closes", lambda count: [1.0] * count)
        return trader, trade_client

    return _make


@pytest.fixture
def client():
    """A FastAPI TestClient with a fresh (stopped) bot manager."""
    from app import app, manager

    manager._runner = None
    return TestClient(app)
