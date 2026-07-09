"""Application settings loaded from environment variables or a .env file.

Replaces the old hand-written ``config.py``. Copy ``.env.example`` to ``.env``
and fill in your Alpaca keys. Values are read case-insensitively, so the .env
file can use conventional upper-case names (e.g. ``ALPACA_API_KEY_ID``).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Alpaca credentials (live and paper).
    alpaca_api_key_id: str = ""
    alpaca_api_secret_key: str = ""
    paper_alpaca_api_key_id: str = ""
    paper_alpaca_api_secret_key: str = ""

    # Trading configuration.
    paper: bool = True
    symbol: str = "VOO"
    strategy: str = "sma_crossover"

    # Position sizing.
    buy_fraction: float = 0.75
    sell_fraction: float = 0.10

    # Runtime behaviour.
    max_wait: int = 300
    trade_interval_days: int = 2
    debug: bool = False

    @property
    def active_key(self) -> str:
        """The API key for the selected (paper or live) endpoint."""
        return self.paper_alpaca_api_key_id if self.paper else self.alpaca_api_key_id

    @property
    def active_secret(self) -> str:
        """The API secret for the selected (paper or live) endpoint."""
        return self.paper_alpaca_api_secret_key if self.paper else self.alpaca_api_secret_key


def get_settings() -> Settings:
    """Build a fresh Settings instance (reads env / .env at call time)."""
    return Settings()
