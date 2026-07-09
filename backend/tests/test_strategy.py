"""Unit tests for the pure strategy logic and indicators."""

from __future__ import annotations

import numpy as np
import pytest

from strategy import (
    STRATEGIES,
    BuyAndHold,
    Macd,
    Rsi,
    Signal,
    SmaCrossover,
    available_strategies,
    ema,
    get_strategy,
    rsi,
    sma,
)


def signals_over(strategy, closes):
    """Every signal produced as the series grows one bar at a time."""
    return [strategy.decide(closes[: i + 1]) for i in range(len(closes))]


# --- indicators --------------------------------------------------------------


def test_sma_is_mean_of_window():
    assert sma([1, 2, 3, 4], 2) == 3.5


def test_ema_matches_series_length():
    assert len(ema([1, 2, 3, 4, 5], 3)) == 5


def test_rsi_all_gains_is_100():
    assert rsi(list(range(1, 40)), period=14) == 100.0


def test_rsi_stays_in_bounds():
    values = [10, 12, 11, 13, 12, 14, 13, 15, 14, 16, 15, 17, 16, 18, 17]
    assert 0 <= rsi(values, period=14) <= 100


# --- SMA crossover -----------------------------------------------------------


def test_sma_crossover_buys_on_upturn():
    closes = list(range(40, 10, -1)) + list(range(10, 45))  # V shape
    assert Signal.BUY in signals_over(SmaCrossover(), closes)


def test_sma_crossover_sells_on_downturn():
    closes = list(range(10, 45)) + list(range(45, 10, -1))  # inverted V
    assert Signal.SELL in signals_over(SmaCrossover(), closes)


def test_sma_crossover_holds_when_flat():
    assert set(signals_over(SmaCrossover(), [10.0] * 30)) == {Signal.HOLD}


def test_sma_crossover_holds_without_enough_data():
    assert SmaCrossover().decide([1, 2, 3]) is Signal.HOLD


def test_sma_crossover_rejects_bad_windows():
    with pytest.raises(ValueError):
        SmaCrossover(short=20, long=5)


# --- RSI ---------------------------------------------------------------------


def test_rsi_sells_when_overbought():
    assert Rsi().decide(list(range(1, 40))) is Signal.SELL


def test_rsi_buys_when_oversold():
    assert Rsi().decide(list(range(40, 1, -1))) is Signal.BUY


def test_rsi_holds_in_the_middle():
    assert Rsi().decide([10, 11] * 20) is Signal.HOLD


# --- MACD --------------------------------------------------------------------


def test_macd_buys_on_upturn():
    closes = list(range(50, 10, -1)) + list(range(10, 60))
    assert Signal.BUY in signals_over(Macd(), closes)


def test_macd_sells_on_downturn():
    closes = list(range(10, 60)) + list(range(60, 10, -1))
    assert Signal.SELL in signals_over(Macd(), closes)


def test_macd_holds_without_enough_data():
    assert Macd().decide([1, 2, 3]) is Signal.HOLD


# --- Buy & Hold + registry ---------------------------------------------------


def test_buy_and_hold_always_buys():
    assert BuyAndHold().decide([1, 2, 3]) is Signal.BUY


def test_buy_and_hold_holds_when_empty():
    assert BuyAndHold().decide([]) is Signal.HOLD


def test_registry_has_all_strategies():
    assert set(STRATEGIES) == {"sma_crossover", "rsi", "macd", "buy_and_hold"}
    assert len(available_strategies()) == 4


def test_get_strategy_builds_instance():
    assert isinstance(get_strategy("sma_crossover"), SmaCrossover)


def test_get_strategy_rejects_unknown():
    with pytest.raises(ValueError):
        get_strategy("does_not_exist")


def test_indicator_arrays_are_numpy():
    macd_line, signal_line = np.asarray([1.0]), np.asarray([1.0])
    assert macd_line.shape == signal_line.shape
