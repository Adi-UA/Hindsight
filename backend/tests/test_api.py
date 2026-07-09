"""API tests covering the safe, keyless endpoints and error paths."""

from __future__ import annotations

_CANNED_BACKTEST = {
    "symbol": "VOO",
    "strategy": "sma_crossover",
    "start": "2020-01-01",
    "end": "2020-06-01",
    "initial_cash": 10_000.0,
    "final_value": 11_000.0,
    "return_pct": 10.0,
    "num_trades": 3,
    "max_drawdown_pct": 5.0,
    "series": [{"date": "2020-01-02", "close": 100.0, "equity": 10_000.0}],
    "markers": [{"date": "2020-01-10", "side": "BUY", "price": 100.0}],
}


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_strategies_lists_all_four(client):
    names = {s["name"] for s in client.get("/api/strategies").json()}
    assert names == {"sma_crossover", "rsi", "macd", "buy_and_hold"}


def test_status_without_runner(client):
    body = client.get("/api/status").json()
    assert body["running"] is False
    assert body["account"] is None


def test_history_without_runner_is_empty(client):
    assert client.get("/api/history").json() == []


def test_backtest_happy_path(client, monkeypatch):
    monkeypatch.setattr("app.run_backtest", lambda *a, **k: _CANNED_BACKTEST)
    resp = client.post(
        "/api/backtest",
        json={
            "strategy": "sma_crossover",
            "symbol": "VOO",
            "start": "2020-01-01",
            "end": "2020-06-01",
            "cash": 10_000,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["final_value"] == 11_000.0


def test_backtest_unknown_strategy_is_400(client):
    resp = client.post(
        "/api/backtest",
        json={"strategy": "nope", "symbol": "VOO", "start": "2020-01-01", "end": "2020-06-01"},
    )
    assert resp.status_code == 400


def test_start_unknown_strategy_is_400(client):
    resp = client.post("/api/trader/start", json={"strategy": "nope"})
    assert resp.status_code == 400
