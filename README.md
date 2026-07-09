# SimpleTrader

[![CI](https://github.com/Adi-UA/SimpleTrader/actions/workflows/ci.yml/badge.svg)](https://github.com/Adi-UA/SimpleTrader/actions/workflows/ci.yml)

A local web app and Python bot for algorithmic **paper trading** on
[Alpaca](https://alpaca.markets). Pick from four strategies, run the bot on a
schedule, and backtest interactively, all from a dashboard on your machine.

> Educational project. It defaults to paper trading and runs only on
> `localhost`. Not financial advice, and not meant for trading real money.

## Features

- **Four pluggable strategies**: SMA crossover, RSI, MACD, and a Buy & Hold
  benchmark. Indicators are plain NumPy, so the same code runs live and in
  backtests.
- **Dashboard** (React + Chakra): start/stop the bot, pick a strategy and
  symbol, watch live status (running, next run, cash, position), and see a
  history of every decision the bot made.
- **Interactive backtesting**: choose a strategy, symbol, date range and
  starting cash, then view return / drawdown / trade metrics and an equity vs.
  price chart with buy/sell markers.
- **Safe by default**: paper trading, bound to `127.0.0.1`.

## Architecture

```
backend/    FastAPI API + trading core (strategy, Trader, BotRunner, backtest)
frontend/   React + Vite + Chakra dashboard
```

The backend serves the built frontend, so a single process runs the whole app.
The bot loop is a controllable background scheduler (`BotRunner`) that runs one
decision cycle per cadence and records what it did.

## Strategies

| Name            | Family              | Logic |
| --------------- | ------------------- | ----- |
| `sma_crossover` | Trend following     | Buy on a golden cross (short SMA crosses above long), sell on a death cross |
| `rsi`           | Mean reversion      | Buy when 14-period RSI is oversold (< 30), sell when overbought (> 70) |
| `macd`          | Momentum            | Buy when the MACD line crosses above its signal line, sell when it crosses below |
| `buy_and_hold`  | Benchmark           | Always buys and holds, a baseline to compare the others against |

The strategy returns a signal (BUY / SELL / HOLD); the bot decides how much to
trade using `BUY_FRACTION` of cash and `SELL_FRACTION` of the position.

## Prerequisites

- Python 3.11+ and Node 18+
- An Alpaca account (paper trading is free)

## Setup

**Backend**

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then fill in your Alpaca paper keys
```

**Frontend**

```bash
cd frontend
npm install
```

## Running

### One process (serves the dashboard)

```bash
cd frontend && npm run build      # builds into backend/static
cd ../backend && source .venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000.

### Dev mode (hot reload)

```bash
# terminal 1
cd backend && source .venv/bin/activate && uvicorn app:app --reload --port 8000
# terminal 2
cd frontend && npm run dev
```

Open http://127.0.0.1:5173 (the dev server proxies `/api` to the backend).

### Headless CLI (no web)

```bash
cd backend && source .venv/bin/activate
python trade.py                                                   # run the bot from .env
python backtest.py --symbol VOO --strategy rsi --start 2020-01-01 --end 2024-01-01
```

## Configuration (`.env`)

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `PAPER` | `true` | Paper trading (safe). Set `false` for real money. |
| `SYMBOL` | `VOO` | Ticker to trade |
| `STRATEGY` | `sma_crossover` | One of the strategy names above |
| `BUY_FRACTION` | `0.75` | Fraction of cash to deploy on a BUY |
| `SELL_FRACTION` | `0.10` | Fraction of the position to sell on a SELL |
| `TRADE_INTERVAL_DAYS` | `2` | Days between trades |
| `MAX_WAIT` | `300` | Seconds to wait for an order to fill |

Paper and live keys are set separately (`PAPER_ALPACA_*` and `ALPACA_*`); the
bot picks the right pair based on `PAPER`.

## Testing

```bash
cd backend && source .venv/bin/activate && ruff check . && pytest
cd frontend && npm test && npm run build
```

## Disclaimer

This project is for educational purposes only. It is not financial advice, and
the author is not responsible for any losses. Trade real money at your own risk.

## License

MIT, see [LICENSE](LICENSE).
