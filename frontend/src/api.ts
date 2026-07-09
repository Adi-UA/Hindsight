// Typed client for the SimpleTrader backtest API.

export interface StrategyInfo {
  name: string;
  description: string;
}

export interface SeriesPoint {
  date: string;
  close: number;
  equity: number;
}

export interface Marker {
  date: string;
  side: string;
  price: number;
}

export interface StrategyResult {
  strategy: string;
  final_value: number;
  return_pct: number;
  num_trades: number;
  max_drawdown_pct: number;
  series: SeriesPoint[];
  markers: Marker[];
}

export interface ComparisonResult {
  symbol: string;
  start: string;
  end: string;
  initial_cash: number;
  results: StrategyResult[];
}

export interface BacktestRequest {
  strategies: string[];
  symbol: string;
  start: string;
  end: string;
  cash: number;
}

const BASE = import.meta.env.VITE_API_BASE ?? "";

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body; keep the status text
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const getStrategies = () => jsonFetch<StrategyInfo[]>("/api/strategies");

export const runBacktest = (body: BacktestRequest) =>
  jsonFetch<ComparisonResult>("/api/backtest", {
    method: "POST",
    body: JSON.stringify(body),
  });
