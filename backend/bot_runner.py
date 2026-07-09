"""A controllable background scheduler around a :class:`~trader.Trader`.

The original trader ran an infinite ``while True`` loop that slept for days.
That cannot be started, stopped or observed from a web UI, so :class:`BotRunner`
wraps the trader in a background thread with a stop event. It runs one decision
cycle per cadence, records every :class:`~trader.Decision`, and exposes when the
next run is scheduled so the dashboard can display live status.

Scheduling is approximate: it targets 09:30 America/New_York on trading days and
skips weekends. It does not account for market holidays, which is acceptable for
a learning project (Alpaca simply rejects orders when the market is closed).
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from trader import Decision, Trader

NY_TZ = ZoneInfo("America/New_York")
_OPEN = time(9, 30)
_CLOSE = time(16, 0)


class BotRunner:
    """Run a :class:`Trader` on a fixed cadence in a background thread."""

    def __init__(
        self,
        trader: Trader,
        interval_days: int = 2,
        quick_test: bool = False,
        history_size: int = 200,
    ) -> None:
        self.trader = trader
        self.interval_days = interval_days
        # quick_test runs every 60s regardless of market hours, for demos/tests.
        self.quick_test = quick_test
        self.tz = trader.tz
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._history: deque[Decision] = deque(maxlen=history_size)
        self._next_run_at: datetime | None = None
        self._last_run_at: datetime | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def next_run_at(self) -> datetime | None:
        return self._next_run_at

    @property
    def last_run_at(self) -> datetime | None:
        return self._last_run_at

    def history(self) -> list[Decision]:
        return list(self._history)

    def start(self) -> None:
        """Start the background loop. Raises if already running."""
        if self.running:
            raise RuntimeError("Bot is already running")
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="bot-runner", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        """Signal the loop to stop and wait briefly for the thread to exit."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self._thread = None
        self._next_run_at = None

    def status(self) -> dict[str, object]:
        """A snapshot of runner state for the dashboard."""
        return {
            "running": self.running,
            "strategy": self.trader.strategy.name,
            "symbol": self.trader.symbol,
            "paper": self.trader.paper,
            "quick_test": self.quick_test,
            "next_run_at": self._next_run_at.isoformat() if self._next_run_at else None,
            "last_run_at": self._last_run_at.isoformat() if self._last_run_at else None,
        }

    # --- internals -----------------------------------------------------------

    def _loop(self) -> None:
        while not self._stop.is_set():
            now = datetime.now(self.tz)
            if self._ready_to_run(now):
                self._run_and_record()
                self._last_run_at = datetime.now(self.tz)
            self._next_run_at = self._compute_next_run(now)
            wait_s = max(1.0, self._seconds_until(self._next_run_at))
            if self.quick_test:
                wait_s = min(wait_s, 60.0)
            # Event.wait returns True immediately when stop() is called, so a
            # multi-day wait is still interrupted the moment we stop.
            if self._stop.wait(wait_s):
                break

    def _run_and_record(self) -> None:
        try:
            self._history.append(self.trader.run_once())
        except Exception:
            logging.exception("Trading run failed")

    def _ready_to_run(self, now: datetime) -> bool:
        if self.quick_test:
            return True
        if now.weekday() >= 5:  # Saturday/Sunday
            return False
        if not (_OPEN <= now.time() <= _CLOSE):
            return False
        if self._last_run_at is None:
            return True
        return (now - self._last_run_at) >= timedelta(days=self.interval_days)

    def _compute_next_run(self, now: datetime) -> datetime:
        if self.quick_test:
            return now + timedelta(seconds=60)

        if self._last_run_at is None:
            candidate = now.replace(
                hour=_OPEN.hour, minute=_OPEN.minute, second=0, microsecond=0
            )
            if now.time() > _OPEN:
                candidate += timedelta(days=1)
        else:
            candidate = (self._last_run_at + timedelta(days=self.interval_days)).replace(
                hour=_OPEN.hour, minute=_OPEN.minute, second=0, microsecond=0
            )

        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
        return candidate

    def _seconds_until(self, when: datetime | None) -> float:
        if when is None:
            return 1.0
        return max(0.0, (when - datetime.now(self.tz)).total_seconds())
