"""FastAPI backend for the SimpleTrader backtest visualizer.

A small, stateless API: list the available strategies and run a backtest over
historical data. There is no live trading, no account, and no secrets, which is
what makes it safe to host publicly. It also serves the built frontend when
present (for local single-process use); when deployed on a static host the
frontend is served separately.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backtest import run_comparison
from paths import STATIC_DIR
from pricecache import RateLimitError
from schemas import BacktestRequest, BacktestResponse, HealthResponse, StrategyInfo
from strategy import available_strategies, get_strategy

app = FastAPI(title="SimpleTrader", version="2.0.0")

# Allow the Vite dev server to call the API during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/api/strategies", response_model=list[StrategyInfo])
def strategies() -> list[dict[str, str]]:
    return available_strategies()


@app.post("/api/backtest", response_model=BacktestResponse)
def backtest(req: BacktestRequest) -> dict:
    try:
        strategies = [get_strategy(name) for name in req.strategies]
        return run_comparison(
            strategies,
            req.symbol,
            req.start.isoformat(),
            req.end.isoformat(),
            cash=req.cash,
        )
    except ValueError as exc:  # unknown strategy or no data for the range
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RateLimitError as exc:  # too many live Yahoo fetches
        raise HTTPException(status_code=429, detail=str(exc)) from exc


# Serve the built frontend if present (local single-process use). On a static
# host the frontend is served by the platform instead.
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
