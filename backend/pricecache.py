"""In-memory price cache and a simple rate limiter for Yahoo Finance calls.

Good enough for a small, mostly single-instance app: it avoids re-downloading
the same data (a TTL cache) and caps how fast we hit Yahoo on cache misses (a
token bucket). State is per-process, so it is not shared across serverless
instances and resets on restart. That trade-off is acceptable here.
"""

from __future__ import annotations

import threading
import time

import pandas as pd


class RateLimitError(RuntimeError):
    """Raised when live data fetches are requested faster than allowed."""


class _TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_per_sec = refill_per_sec
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def take(self) -> bool:
        """Consume one token; return False if none are available."""
        with self._lock:
            now = time.monotonic()
            self.tokens = min(
                self.capacity, self.tokens + (now - self._last) * self.refill_per_sec
            )
            self._last = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


class PriceCache:
    """TTL cache for OHLCV frames plus a token-bucket fetch limiter."""

    def __init__(
        self,
        ttl_seconds: float = 3600,
        capacity: int = 30,
        refill_per_sec: float = 0.5,
    ) -> None:
        self._ttl = ttl_seconds
        self._store: dict[tuple[str, str, str], tuple[float, pd.DataFrame]] = {}
        self._lock = threading.Lock()
        self._bucket = _TokenBucket(capacity, refill_per_sec)

    @staticmethod
    def key(symbol: str, start: str, end: str) -> tuple[str, str, str]:
        return (symbol.upper(), str(start), str(end))

    def get(self, key: tuple[str, str, str]) -> pd.DataFrame | None:
        with self._lock:
            hit = self._store.get(key)
            if hit is None:
                return None
            stored_at, df = hit
            if time.monotonic() - stored_at < self._ttl:
                return df
            del self._store[key]
            return None

    def put(self, key: tuple[str, str, str], df: pd.DataFrame) -> None:
        with self._lock:
            self._store[key] = (time.monotonic(), df)

    def allow_fetch(self) -> bool:
        return self._bucket.take()
