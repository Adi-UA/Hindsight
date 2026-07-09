"""Trading strategies for Hindsight.

Each strategy is a pure function of a sequence of closing prices: given the
recent closes (oldest first), :meth:`Strategy.decide` returns a :class:`Signal`
of ``BUY``, ``SELL`` or ``HOLD``. Strategies carry no brokerage or network
dependency, which makes them trivial to unit test and lets the backtester run
the exact same logic that runs live.

The indicators (SMA, EMA, RSI, MACD) are implemented from scratch with NumPy so
the project stays dependency-light and the maths stays visible for learning.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import StrEnum

import numpy as np


class Signal(StrEnum):
    """A trading decision produced by a strategy."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# --- indicator helpers -------------------------------------------------------


def sma(values: Sequence[float] | np.ndarray, period: int) -> float:
    """Simple moving average of the most recent ``period`` values."""
    arr = np.asarray(values, dtype=float)
    return float(np.mean(arr[-period:]))


def ema(values: Sequence[float] | np.ndarray, period: int) -> np.ndarray:
    """Exponential moving average as a series the same length as ``values``.

    Seeded with the first value and smoothed with ``alpha = 2 / (period + 1)``.
    """
    arr = np.asarray(values, dtype=float)
    alpha = 2.0 / (period + 1)
    out = np.empty_like(arr)
    out[0] = arr[0]
    for i in range(1, len(arr)):
        out[i] = alpha * arr[i] + (1 - alpha) * out[i - 1]
    return out


def rsi(closes: Sequence[float] | np.ndarray, period: int = 14) -> float:
    """Wilder's Relative Strength Index over the most recent data.

    Returns a value in ``[0, 100]``; ``100`` when the window has no losses.
    Requires at least ``period + 1`` closes.
    """
    arr = np.asarray(closes, dtype=float)
    deltas = np.diff(arr)
    gains = np.clip(deltas, 0.0, None)
    losses = -np.clip(deltas, None, 0.0)

    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def macd(
    closes: Sequence[float] | np.ndarray,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the MACD line and its signal line as two series.

    MACD line = EMA(fast) - EMA(slow); signal line = EMA(MACD line, signal).
    """
    arr = np.asarray(closes, dtype=float)
    macd_line = ema(arr, fast) - ema(arr, slow)
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line


# --- strategies --------------------------------------------------------------


class Strategy(ABC):
    """Base class for trading strategies.

    A strategy inspects a sequence of closing prices (oldest first) and returns
    a :class:`Signal`. It never sizes the order or talks to a broker; that is
    the caller's job. When there is not enough history to decide, a strategy
    returns ``HOLD``.
    """

    #: Short machine name used to select the strategy from config or the API.
    name: str = "base"
    #: Human-readable description shown in the UI.
    description: str = ""
    #: When True, invest (nearly) all cash on a BUY and then hold, so benchmark
    #: strategies are not repeatedly scaled in. Active strategies leave this False.
    full_invest: bool = False

    @property
    @abstractmethod
    def min_bars(self) -> int:
        """Minimum number of closing prices required to produce a signal."""

    @abstractmethod
    def decide(self, closes: Sequence[float]) -> Signal:
        """Return ``BUY``, ``SELL`` or ``HOLD`` for the given closes."""


class SmaCrossover(Strategy):
    """Simple moving average crossover (trend following).

    Buys on a *golden cross* (the short SMA crosses above the long SMA) and
    sells on a *death cross* (short crosses below long). It compares the SMA
    relationship today against yesterday, so it fires only on the crossover
    event itself and holds the rest of the time.
    """

    name = "sma_crossover"
    description = (
        "Trend following. Buys when the short SMA crosses above the long SMA "
        "(golden cross) and sells on the death cross."
    )

    def __init__(self, short: int = 5, long: int = 20) -> None:
        if short < 1 or long < 1:
            raise ValueError("SMA windows must be positive")
        if short >= long:
            raise ValueError("short window must be smaller than long window")
        self.short = short
        self.long = long

    @property
    def min_bars(self) -> int:
        # Need one extra bar to compute the previous SMAs for the crossover.
        return self.long + 1

    def decide(self, closes: Sequence[float]) -> Signal:
        arr = np.asarray(closes, dtype=float)
        if len(arr) < self.min_bars:
            return Signal.HOLD

        short_now = sma(arr, self.short)
        long_now = sma(arr, self.long)
        short_prev = sma(arr[:-1], self.short)
        long_prev = sma(arr[:-1], self.long)

        if short_prev <= long_prev and short_now > long_now:
            return Signal.BUY
        if short_prev >= long_prev and short_now < long_now:
            return Signal.SELL
        return Signal.HOLD


class Rsi(Strategy):
    """Relative Strength Index (mean reversion).

    Buys when RSI falls below ``low`` (oversold) and sells when it rises above
    ``high`` (overbought).
    """

    name = "rsi"
    description = (
        "Mean reversion. Buys when the 14-period RSI is oversold (below 30) "
        "and sells when it is overbought (above 70)."
    )

    def __init__(self, period: int = 14, low: float = 30.0, high: float = 70.0) -> None:
        if period < 2:
            raise ValueError("RSI period must be at least 2")
        if not 0 <= low < high <= 100:
            raise ValueError("require 0 <= low < high <= 100")
        self.period = period
        self.low = low
        self.high = high

    @property
    def min_bars(self) -> int:
        return self.period + 1

    def decide(self, closes: Sequence[float]) -> Signal:
        arr = np.asarray(closes, dtype=float)
        if len(arr) < self.min_bars:
            return Signal.HOLD

        value = rsi(arr, self.period)
        if value < self.low:
            return Signal.BUY
        if value > self.high:
            return Signal.SELL
        return Signal.HOLD


class Macd(Strategy):
    """Moving Average Convergence Divergence (momentum).

    Buys when the MACD line crosses above its signal line and sells when it
    crosses below.
    """

    name = "macd"
    description = (
        "Momentum. Buys when the MACD line (EMA12 - EMA26) crosses above its "
        "signal line (EMA9) and sells when it crosses below."
    )

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        if fast < 1 or slow < 1 or signal < 1:
            raise ValueError("MACD periods must be positive")
        if fast >= slow:
            raise ValueError("fast period must be smaller than slow period")
        self.fast = fast
        self.slow = slow
        self.signal = signal

    @property
    def min_bars(self) -> int:
        return self.slow + self.signal

    def decide(self, closes: Sequence[float]) -> Signal:
        arr = np.asarray(closes, dtype=float)
        if len(arr) < self.min_bars:
            return Signal.HOLD

        macd_line, signal_line = macd(arr, self.fast, self.slow, self.signal)
        if macd_line[-2] <= signal_line[-2] and macd_line[-1] > signal_line[-1]:
            return Signal.BUY
        if macd_line[-2] >= signal_line[-2] and macd_line[-1] < signal_line[-1]:
            return Signal.SELL
        return Signal.HOLD


class BuyAndHold(Strategy):
    """Baseline that stays invested.

    Always signals ``BUY`` so the position is built and held. Useful mainly as
    a benchmark in the backtester: does an active strategy actually beat simply
    holding the stock?
    """

    name = "buy_and_hold"
    description = "Baseline benchmark. Invests once and holds for the whole period."

    full_invest = True

    @property
    def min_bars(self) -> int:
        return 1

    def decide(self, closes: Sequence[float]) -> Signal:
        return Signal.BUY if len(closes) >= self.min_bars else Signal.HOLD


# --- registry ----------------------------------------------------------------

_STRATEGY_CLASSES: tuple[type[Strategy], ...] = (
    SmaCrossover,
    Rsi,
    Macd,
    BuyAndHold,
)

#: Map of strategy name -> class, used to build a strategy by name.
STRATEGIES: dict[str, type[Strategy]] = {cls.name: cls for cls in _STRATEGY_CLASSES}


def get_strategy(name: str, **params: object) -> Strategy:
    """Build a strategy instance by name, passing through any parameters."""
    try:
        cls = STRATEGIES[name]
    except KeyError:
        available = ", ".join(STRATEGIES)
        raise ValueError(f"Unknown strategy '{name}'. Available: {available}") from None
    return cls(**params)  # type: ignore[arg-type]


def available_strategies() -> list[dict[str, str]]:
    """Return name + description for every registered strategy (UI friendly)."""
    return [{"name": cls.name, "description": cls.description} for cls in _STRATEGY_CLASSES]
