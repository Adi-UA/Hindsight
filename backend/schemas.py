"""Pydantic request/response models for the SimpleTrader API."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class StrategyInfo(BaseModel):
    name: str
    description: str


class StartRequest(BaseModel):
    """Overrides for a bot run. Unset fields fall back to server settings."""

    strategy: str | None = None
    symbol: str | None = None
    paper: bool | None = None
    quick_test: bool = False


class AccountSnapshot(BaseModel):
    cash: float
    portfolio_value: float
    position_qty: float
    position_value: float


class StatusResponse(BaseModel):
    running: bool
    strategy: str
    symbol: str
    paper: bool
    quick_test: bool = False
    next_run_at: str | None = None
    last_run_at: str | None = None
    account: AccountSnapshot | None = None


class DecisionOut(BaseModel):
    timestamp: str
    symbol: str
    strategy: str
    signal: str
    action: str
    amount: float | None = None
    status: str


class BacktestRequest(BaseModel):
    strategy: str = "sma_crossover"
    symbol: str = "VOO"
    start: date
    end: date
    cash: float = Field(default=10_000.0, gt=0)


class SeriesPoint(BaseModel):
    date: str
    close: float
    equity: float


class Marker(BaseModel):
    date: str
    side: str
    price: float


class BacktestResponse(BaseModel):
    symbol: str
    strategy: str
    start: str
    end: str
    initial_cash: float
    final_value: float
    return_pct: float
    num_trades: int
    max_drawdown_pct: float
    series: list[SeriesPoint]
    markers: list[Marker]
