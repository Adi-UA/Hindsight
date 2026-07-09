"""Tests for backtests and comparison using a synthetic in-memory price feed."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest import _feed_from_df, _load_yf_df, run_backtest, run_comparison
from strategy import BuyAndHold, Rsi, SmaCrossover


def _synthetic_df(prices) -> pd.DataFrame:
    prices = np.asarray(prices, dtype=float)
    index = pd.bdate_range("2021-01-01", periods=len(prices))
    return pd.DataFrame(
        {
            "Open": prices,
            "High": prices * 1.01,
            "Low": prices * 0.99,
            "Close": prices,
            "Volume": 1_000_000,
        },
        index=index,
    )


def _synthetic_feed(prices):
    return _feed_from_df(_synthetic_df(prices))


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


def test_run_comparison_returns_one_result_per_strategy_on_shared_dates():
    prices = list(np.linspace(200, 100, 60)) + list(np.linspace(100, 200, 60))
    out = run_comparison(
        [SmaCrossover(), Rsi(), BuyAndHold()],
        "TEST",
        "2021-01-01",
        "2021-06-30",
        cash=10_000,
        df=_synthetic_df(prices),
    )
    assert [r["strategy"] for r in out["results"]] == ["sma_crossover", "rsi", "buy_and_hold"]
    dates0 = [p["date"] for p in out["results"][0]["series"]]
    for r in out["results"][1:]:
        assert [p["date"] for p in r["series"]] == dates0


def test_load_yf_df_raises_when_no_data(monkeypatch):
    # Yahoo occasionally returns an empty frame (rate limit, delisting, broken
    # yfinance version). Surface a clear error rather than crashing.
    monkeypatch.setattr("backtest.yf.download", lambda *a, **k: pd.DataFrame())
    with pytest.raises(ValueError):
        _load_yf_df("ZZZ_DOES_NOT_EXIST", "2020-01-01", "2020-02-01")
