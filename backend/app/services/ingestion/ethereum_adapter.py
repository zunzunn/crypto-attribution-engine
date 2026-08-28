"""Ethereum chain adapter: fetch -> normalize -> hand back canonical txs.

This is the single entry point the ingestion orchestrator talks to for the
``ethereum`` chain. It isolates Etherscan specifics so no other module in the
codebase knows about Etherscan.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import Settings
from app.schemas import Transaction
from app.services.ingestion.ethereum_client import EtherscanClient
from app.services.ingestion.ethereum_normalizer import normalize_etherscan_native_batch


class EthereumAdapter:
    chain_id = "ethereum"
    default_network: str | None = None

    def __init__(
        self,
        *,
        client: EtherscanClient,
        network: str,
        value_decimals: int = 18,
    ) -> None:
        self._client = client
        self.network = network
        self.default_network = network
        self._value_decimals = value_decimals

    @classmethod
    def from_settings(cls, settings: Settings) -> EthereumAdapter:
        client = EtherscanClient(
            api_key=settings.etherscan_api_key,
            base_url=settings.etherscan_resolved_base_url,
            chain_id=settings.etherscan_resolved_chain_id,
            timeout_seconds=settings.etherscan_timeout_seconds,
            page_size=settings.etherscan_page_size,
            max_pages=settings.etherscan_max_pages,
        )
        return cls(
            client=client,
            network=settings.etherscan_network,
            value_decimals=settings.default_ethereum_value_decimals,
        )

    @property
    def source(self) -> str:
        return f"etherscan:{self.network}"

    async def get_normalized_transactions(self, address: str) -> list[Transaction]:
        raw = await self._client.get_native_transactions(address)
        return normalize_etherscan_native_batch(
            raw,
            chain_id=self.chain_id,
            network=self.network,
            source=self.source,
            fetched_at=datetime.now(timezone.utc),
            value_decimals=self._value_decimals,
        )