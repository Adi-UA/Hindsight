"""API tests covering the keyless backtest-comparison endpoints."""

from __future__ import annotations

_CANNED = {
    "symbol": "VOO",
    "start": "2020-01-01",
    "end": "2020-06-01",
    "initial_cash": 10_000.0,
    "results": [
        {
            "strategy": "sma_crossover",
            "final_value": 11_000.0,
            "return_pct": 10.0,
            "num_trades": 3,
            "max_drawdown_pct": 5.0,
            "series": [{"date": "2020-01-02", "close": 100.0, "equity": 10_000.0}],
            "markers": [],
        }
    ],
}


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_strategies_lists_all_four(client):
    names = {s["name"] for s in client.get("/api/strategies").json()}
    assert names == {"sma_crossover", "rsi", "macd", "buy_and_hold"}


def test_backtest_happy_path(client, monkeypatch):
    monkeypatch.setattr("app.run_comparison", lambda *a, **k: _CANNED)
    resp = client.post(
        "/api/backtest",
        json={
            "strategies": ["sma_crossover"],
            "symbol": "VOO",
            "start": "2020-01-01",
            "end": "2020-06-01",
            "cash": 10_000,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["results"][0]["final_value"] == 11_000.0


def test_backtest_unknown_strategy_is_400(client):
    resp = client.post(
        "/api/backtest",
        json={
            "strategies": ["nope"],
            "symbol": "VOO",
            "start": "2020-01-01",
            "end": "2020-06-01",
        },
    )
    assert resp.status_code == 400


def test_backtest_too_many_strategies_is_422(client):
    resp = client.post(
        "/api/backtest",
        json={
            "strategies": ["sma_crossover", "rsi", "macd", "buy_and_hold"],
            "symbol": "VOO",
            "start": "2020-01-01",
            "end": "2020-06-01",
        },
    )
    assert resp.status_code == 422


def test_backtest_rate_limited_is_429(client, monkeypatch):
    from pricecache import RateLimitError

    def _raise(*a, **k):
        raise RateLimitError("slow down")

    monkeypatch.setattr("app.run_comparison", _raise)
    resp = client.post(
        "/api/backtest",
        json={
            "strategies": ["sma_crossover"],
            "symbol": "VOO",
            "start": "2020-01-01",
            "end": "2020-06-01",
        },
    )
    assert resp.status_code == 429
