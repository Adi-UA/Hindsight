"""FastAPI backend for SimpleTrader.

Exposes the strategy list, live bot control (start/stop/status/history) and a
keyless backtest endpoint, and serves the built React dashboard. Intended to run
locally only (bind to 127.0.0.1) and defaults to paper trading so the Start
button cannot place real orders unless explicitly overridden.
"""

from __future__ import annotations

import logging
import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backtest import run_backtest
from bot_runner import BotRunner
from paths import STATIC_DIR
from schemas import (
    AccountSnapshot,
    BacktestRequest,
    BacktestResponse,
    DecisionOut,
    HealthResponse,
    StartRequest,
    StatusResponse,
    StrategyInfo,
)
from settings import Settings, get_settings
from strategy import available_strategies, get_strategy
from trader import Trader

logger = logging.getLogger(__name__)


class BotManager:
    """Owns the single active BotRunner and guards start/stop concurrency."""

    def __init__(self) -> None:
        self._runner: BotRunner | None = None
        self._lock = threading.Lock()

    @property
    def runner(self) -> BotRunner | None:
        return self._runner

    def start(
        self,
        *,
        strategy_name: str,
        symbol: str,
        paper: bool,
        quick_test: bool,
        settings: Settings,
    ) -> BotRunner:
        with self._lock:
            if self._runner is not None and self._runner.running:
                raise RuntimeError("Bot is already running")

            strategy = get_strategy(strategy_name)  # raises ValueError if unknown
            key = settings.paper_alpaca_api_key_id if paper else settings.alpaca_api_key_id
            secret = (
                settings.paper_alpaca_api_secret_key
                if paper
                else settings.alpaca_api_secret_key
            )
            trader = Trader(
                strategy=strategy,
                symbol=symbol,
                api_key=key,
                secret_key=secret,
                paper=paper,
                buy_fraction=settings.buy_fraction,
                sell_fraction=settings.sell_fraction,
                max_wait=settings.max_wait,
                debug=settings.debug,
            )
            runner = BotRunner(
                trader,
                interval_days=settings.trade_interval_days,
                quick_test=quick_test,
            )
            runner.start()
            self._runner = runner
            return runner

    def stop(self) -> None:
        with self._lock:
            if self._runner is not None:
                self._runner.stop()


manager = BotManager()
app = FastAPI(title="SimpleTrader", version="1.0.0")

# Local dev: the Vite dev server runs on 5173 and calls this API on 8000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_status() -> StatusResponse:
    settings = get_settings()
    runner = manager.runner
    if runner is None:
        return StatusResponse(
            running=False,
            strategy=settings.strategy,
            symbol=settings.symbol,
            paper=settings.paper,
        )

    account = None
    try:
        account = AccountSnapshot(**runner.trader.account_snapshot())
    except Exception:
        logger.warning("Could not fetch account snapshot", exc_info=True)
    return StatusResponse(account=account, **runner.status())


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/api/strategies", response_model=list[StrategyInfo])
def strategies() -> list[dict[str, str]]:
    return available_strategies()


@app.get("/api/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return _build_status()


@app.post("/api/trader/start", response_model=StatusResponse)
def start_trader(req: StartRequest) -> StatusResponse:
    settings = get_settings()
    try:
        manager.start(
            strategy_name=req.strategy or settings.strategy,
            symbol=req.symbol or settings.symbol,
            paper=settings.paper if req.paper is None else req.paper,
            quick_test=req.quick_test,
            settings=settings,
        )
    except ValueError as exc:  # unknown strategy
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:  # already running / account not valid
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # brokerage/connection failure
        raise HTTPException(status_code=502, detail=f"Failed to start bot: {exc}") from exc
    return _build_status()


@app.post("/api/trader/stop", response_model=StatusResponse)
def stop_trader() -> StatusResponse:
    manager.stop()
    return _build_status()


@app.get("/api/history", response_model=list[DecisionOut])
def history() -> list[DecisionOut]:
    runner = manager.runner
    if runner is None:
        return []
    return [DecisionOut(**decision.as_dict()) for decision in runner.history()]


@app.post("/api/backtest", response_model=BacktestResponse)
def backtest(req: BacktestRequest) -> dict:
    try:
        strategy = get_strategy(req.strategy)
        return run_backtest(
            strategy,
            req.symbol,
            req.start.isoformat(),
            req.end.isoformat(),
            cash=req.cash,
        )
    except ValueError as exc:  # unknown strategy or no data
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# Serve the built frontend if it has been built into ./static (guarded so the
# API and tests work without a frontend build present).
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
