"""Chain-aware address validation and normalization.

Only Ethereum is implemented in Phase 1. Addresses are normalized to
lowercase for canonical matching; EIP-55 checksum validation is a documented
future enhancement (see REQUIREMENTS.md).
"""

from __future__ import annotations

import re

from app.core.errors import ChainNotSupportedError, InvalidAddressError

SUPPORTED_CHAINS = frozenset({"ethereum"})

_ETHEREUM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def validate_ethereum_address(address: str) -> str:
    """Validate an Ethereum address and return its lowercase form.

    Raises InvalidAddressError when malformed.
    """
    if not isinstance(address, str) or not address.strip():
        raise InvalidAddressError("ethereum", str(address), "address is empty")
    value = address.strip()
    if not _ETHEREUM_ADDRESS_RE.match(value):
        raise InvalidAddressError(
            "ethereum", address, "expected 40 hex characters prefixed with 0x"
        )
    return value.lower()


def validate_chain_address(chain_id: str, address: str) -> str:
    """Validate an address for a chain. Raises ChainNotSupportedError."""
    if chain_id not in SUPPORTED_CHAINS:
        raise ChainNotSupportedError(chain_id)
    if chain_id == "ethereum":
        return validate_ethereum_address(address)
    raise ChainNotSupportedError(chain_id)  # unreachable, defensive