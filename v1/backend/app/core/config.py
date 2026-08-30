"""Central configuration loaded from environment variables / .env file.

All secrets (API keys, database passwords) are read from the environment or
``v1/backend/.env`` (which is git-ignored). Nothing is hardcoded and nothing is
committed. See ``v1/backend/.env.example`` for the documented set of variables.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env (repo root is two levels up from this file: app/core -> app -> backend)
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "crypto-attribution-engine"
    app_env: str = "dev"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Database
    database_url: str = "postgresql+asyncpg://shouryasinha@localhost:5432/crypto_attribution"
    test_database_url: str | None = None
    db_auto_create: bool = True

    # Ethereum / Etherscan
    etherscan_api_key: str = ""
    etherscan_network: str = "mainnet"
    etherscan_base_url: str | None = None
    etherscan_chain_id: int | None = None
    etherscan_timeout_seconds: float = 30.0
    etherscan_page_size: int = 1000
    etherscan_max_pages: int = 20

    # Skip the block/timestamp table if a chain does not index it yet.
    default_ethereum_value_decimals: int = 18

    # ------------------------------------------------------------------ #
    # Derived helpers
    # ------------------------------------------------------------------ #
    @property
    def etherscan_resolved_base_url(self) -> str:
        base = self.etherscan_base_url
        if base:
            return base.rstrip("/")
        return "https://api.etherscan.io/v2/api"

    @property
    def etherscan_resolved_chain_id(self) -> int:
        """Resolve chain id from ETHERSCAN_NETWORK (V2 Etherscan API)."""
        overrides = self.etherscan_chain_id
        if overrides:
            return overrides
        mapping = {
            "mainnet": 1,
            "sepolia": 11155111,
        }
        if self.etherscan_network not in mapping:
            raise ValueError(
                f"Unsupported ETHERSCAN_NETWORK={self.etherscan_network!r}. "
                f"Supported: {', '.join(sorted(mapping))}. Set ETHERSCAN_CHAIN_ID to override."
            )
        return mapping[self.etherscan_network]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()