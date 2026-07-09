# Hindsight

[![CI](https://github.com/Adi-UA/Hindsight/actions/workflows/ci.yml/badge.svg)](https://github.com/Adi-UA/Hindsight/actions/workflows/ci.yml)

A backtest visualizer: see what *would* have happened if you had traded with
classic strategies. Pick a strategy and up to three symbols (say VOO vs QQQM)
over a date range, and compare how they would have performed side by side. No
account or API keys, it uses public Yahoo Finance data.

> Educational only. Past performance does not predict future results, and this
> is not financial advice.

## Strategies

| Name | Family | Logic |
| --- | --- | --- |
| `sma_crossover` | Trend following | Buy on a golden cross (short SMA crosses above long), sell on a death cross |
| `rsi` | Mean reversion | Buy when 14-period RSI is oversold (< 30), sell when overbought (> 70) |
| `macd` | Momentum | Buy when the MACD line crosses above its signal line, sell when it crosses below |
| `buy_and_hold` | Benchmark | Stays invested, a baseline to compare the others against |

## How it works

The FastAPI backend fetches daily prices for each symbol (cached) and runs the
chosen strategy over each with backtrader, returning equity curves plus metrics
(return, trades, max drawdown). The React frontend overlays the results on one
chart. Downloaded data is cached in memory and Yahoo requests are rate limited,
so the app stays light and kind to the data source.

```
backend/    FastAPI API + backtest engine (strategy, backtest, price cache)
frontend/   React + Vite + Chakra visualizer
```

## Run locally

**Backend**

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Frontend**

```bash
cd frontend
npm install
```

**One process (serves the built UI):**

```bash
cd frontend && npm run build          # builds into backend/static
cd ../backend && source .venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000.

**Dev mode (hot reload):**

```bash
# terminal 1
cd backend && source .venv/bin/activate && uvicorn app:app --reload --port 8000
# terminal 2
cd frontend && npm run dev            # proxies /api to the backend
```

**CLI (no web):**

```bash
cd backend && source .venv/bin/activate
python backtest.py --strategy rsi --symbols VOO,QQQM \
  --start 2020-01-01 --end 2024-01-01
```

## API

- `GET /api/strategies` — available strategies and descriptions
- `POST /api/backtest` — `{ strategy, symbols: string[1..3], start, end, cash }`
  returns per-symbol metrics and equity/price series

## Testing

```bash
cd backend && source .venv/bin/activate && ruff check . && pytest
cd frontend && npm test && npm run build
```

## License

MIT, see [LICENSE](LICENSE).
