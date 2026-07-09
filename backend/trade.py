#!/usr/bin/env python3
"""CLI entrypoint: run the trading bot from .env settings until interrupted.

The web dashboard is the primary way to control the bot, but this offers a
headless option. Run it from the backend directory so the .env file is found:

    python trade.py
"""

from __future__ import annotations

import time

from bot_runner import BotRunner
from settings import get_settings
from strategy import get_strategy
from trader import Trader


def main() -> None:
    settings = get_settings()
    trader = Trader(
        strategy=get_strategy(settings.strategy),
        symbol=settings.symbol,
        api_key=settings.active_key,
        secret_key=settings.active_secret,
        paper=settings.paper,
        buy_fraction=settings.buy_fraction,
        sell_fraction=settings.sell_fraction,
        max_wait=settings.max_wait,
        debug=settings.debug,
    )
    runner = BotRunner(trader, interval_days=settings.trade_interval_days)
    runner.start()
    print(
        f"Bot started: strategy={settings.strategy} symbol={settings.symbol} "
        f"paper={settings.paper}. Press Ctrl+C to stop."
    )
    try:
        while runner.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        runner.stop()
        print("Stopped.")


if __name__ == "__main__":
    main()
