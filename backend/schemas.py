"""Pydantic request/response models for the Hindsight API."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class StrategyInfo(BaseModel):
    name: str
    description: str


class BacktestRequest(BaseModel):
    # One strategy applied to one to three symbols, compared over the same range.
    strategy: str = "sma_crossover"
    symbols: list[str] = Field(min_length=1, max_length=3)
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


class SymbolResult(BaseModel):
    symbol: str
    strategy: str
    final_value: float
    return_pct: float
    num_trades: int
    max_drawdown_pct: float
    series: list[SeriesPoint]
    markers: list[Marker]


class BacktestResponse(BaseModel):
    strategy: str
    start: str
    end: str
    initial_cash: float
    results: list[SymbolResult]
