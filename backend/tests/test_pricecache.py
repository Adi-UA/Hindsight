"""Tests for the in-memory price cache and rate limiter."""

from __future__ import annotations

import pandas as pd

from pricecache import PriceCache


def test_cache_put_get_roundtrip():
    cache = PriceCache()
    key = cache.key("voo", "2020-01-01", "2020-02-01")
    assert cache.get(key) is None
    df = pd.DataFrame({"Close": [1, 2, 3]})
    cache.put(key, df)
    assert cache.get(key) is df


def test_key_is_case_insensitive_on_symbol():
    cache = PriceCache()
    assert cache.key("voo", "a", "b") == cache.key("VOO", "a", "b")


def test_ttl_expiry_returns_none():
    cache = PriceCache(ttl_seconds=0)
    key = cache.key("x", "a", "b")
    cache.put(key, pd.DataFrame({"Close": [1]}))
    assert cache.get(key) is None


def test_rate_limiter_blocks_after_capacity():
    cache = PriceCache(capacity=2, refill_per_sec=0)
    assert cache.allow_fetch() is True
    assert cache.allow_fetch() is True
    assert cache.allow_fetch() is False
