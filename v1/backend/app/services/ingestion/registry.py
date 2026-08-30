"""Adapter registry: map a chain id to its adapter instance.

Future Bitcoin / Tron / Polygon / Solana adapters register here; the API and
orchestration stay chain-agnostic.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.errors import ChainNotSupportedError
from app.services.ingestion.base import ChainAdapter
from app.services.ingestion.ethereum_adapter import EthereumAdapter


class IngestionRegistry:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._adapters: dict[str, ChainAdapter] = {
            "ethereum": EthereumAdapter.from_settings(settings),
        }

    def get(self, chain_id: str) -> ChainAdapter:
        adapter = self._adapters.get(chain_id)
        if adapter is None:
            raise ChainNotSupportedError(chain_id)
        return adapter

    @property
    def supported_chains(self) -> list[str]:
        return sorted(self._adapters)