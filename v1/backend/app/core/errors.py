"""Domain-level error hierarchy.

HTTP mapping happens in the API layer; services raise these typed errors and
never touch HTTP concerns directly.
"""

from __future__ import annotations


class AttributionEngineError(Exception):
    """Base error for the whole application."""


class ChainNotSupportedError(AttributionEngineError):
    def __init__(self, chain_id: str) -> None:
        self.chain_id = chain_id
        super().__init__(f"Chain {chain_id!r} is not supported yet. Supported chains: ethereum.")


class InvalidAddressError(AttributionEngineError, ValueError):
    def __init__(self, chain_id: str, address: str, reason: str) -> None:
        self.chain_id = chain_id
        self.address = address
        self.reason = reason
        super().__init__(
            f"Invalid {chain_id} address {address!r}: {reason}"
        )


class ProviderError(AttributionEngineError):
    """An upstream blockchain data provider failed or returned an error."""


class RateLimitError(ProviderError):
    """Upstream provider rate limit reached."""


class IngestionError(AttributionEngineError):
    """Generic failure while ingesting/normalizing chain data."""