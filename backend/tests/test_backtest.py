"""Tests for the headless backtest using a synthetic in-memory price feed."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import _feed_from_df, _load_yf_feed, run_backtest
from strategy import BuyAndHold, SmaCrossover


def _synthetic_feed(prices):
    prices = np.asarray(prices, dtype=float)
    index = pd.bdate_range("2021-01-01", periods=len(prices))
    df = pd.DataFrame(
        {
            "Open": prices,
            "High": prices * 1.01,
            "Low": prices * 0.99,
            "Close": prices,
            "Volume": 1_000_000,
        },
        index=index,
    )
    return _feed_from_df(df)


def test_buy_and_hold_produces_trades_and_series():
    prices = np.linspace(100, 200, 120)
    result = run_backtest(
        BuyAndHold(), "TEST", "2021-01-01", "2021-06-30", cash=10_000, data=_synthetic_feed(prices)
    )
    assert result["num_trades"] >= 1
    assert len(result["series"]) > 100
    assert result["final_value"] > 0
    assert {"return_pct", "max_drawdown_pct", "markers", "series"} <= set(result)


def test_sma_backtest_runs_and_reports_metadata():
    prices = list(np.linspace(200, 100, 60)) + list(np.linspace(100, 200, 60))
    result = run_backtest(
        SmaCrossover(), "TEST", "2021-01-01", "2021-06-30", cash=5_000, data=_synthetic_feed(prices)
    )
    assert result["strategy"] == "sma_crossover"
    assert result["symbol"] == "TEST"
    assert len(result["series"]) > 50
    assert isinstance(result["return_pct"], float)


def test_load_yf_feed_raises_when_no_data(monkeypatch):
    # Yahoo occasionally returns an empty frame (rate limit, delisting, or a
    # broken yfinance version). We should surface a clear error, not crash.
    monkeypatch.setattr("backtest.yf.download", lambda *a, **k: pd.DataFrame())
    with pytest.raises(ValueError):
        _load_yf_feed("VOO", "2020-01-01", "2020-02-01")
