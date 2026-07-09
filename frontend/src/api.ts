// Typed client for the SimpleTrader backend API.

export interface StrategyInfo {
  name: string;
  description: string;
}

export interface Account {
  cash: number;
  portfolio_value: number;
  position_qty: number;
  position_value: number;
}

export interface Status {
  running: boolean;
  strategy: string;
  symbol: string;
  paper: boolean;
  quick_test: boolean;
  next_run_at: string | null;
  last_run_at: string | null;
  account: Account | null;
}

export interface Decision {
  timestamp: string;
  symbol: string;
  strategy: string;
  signal: string;
  action: string;
  amount: number | null;
  status: string;
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

export interface BacktestResult {
  symbol: string;
  strategy: string;
  start: string;
  end: string;
  initial_cash: number;
  final_value: number;
  return_pct: number;
  num_trades: number;
  max_drawdown_pct: number;
  series: SeriesPoint[];
  markers: Marker[];
}

export interface StartRequest {
  strategy?: string;
  symbol?: string;
  paper?: boolean;
  quick_test?: boolean;
}

export interface BacktestRequest {
  strategy: string;
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
export const getStatus = () => jsonFetch<Status>("/api/status");
export const getHistory = () => jsonFetch<Decision[]>("/api/history");

export const startTrader = (body: StartRequest) =>
  jsonFetch<Status>("/api/trader/start", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const stopTrader = () =>
  jsonFetch<Status>("/api/trader/stop", { method: "POST" });

export const runBacktest = (body: BacktestRequest) =>
  jsonFetch<BacktestResult>("/api/backtest", {
    method: "POST",
    body: JSON.stringify(body),
  });
