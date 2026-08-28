"""Canonical, blockchain-agnostic transaction model.

This single schema is the contract between every chain adapter and the rest
of the system (persistence, later traversal/attribution phases). It is
deliberately chain-agnostic:

* Utxo chains (Bitcoin) populate ``senders``/``recipients`` as lists; fee
  chains expose one-to-many inputs/outputs.
* Account-based chains (Ethereum, Polygon, Tron, Solana) populate the single
  ``from_address``/``to_address`` fields as well as the same lists (one
  element each).
* ``value`` is ALWAYS a base-unit integer *string* (wei / satoshi / lamports /
  sun). Never a float. ``value_decimals`` describes the exponent so a
  human-readable amount can be derived without floating point math.

``transaction_type`` distinguishes native transfers from token transfers
(``token_transfers``) so a token-heavy chain (e.g. Tron USDT) maps cleanly.
``token_transfers`` is populated from Phase 1-follow-on; native only now.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.time import as_aware_utc


class AddressAmount(BaseModel):
    """An address participating in a transfer (UTXO input/output or account
    sender/recipient) and the value attributed to it, in base units."""

    address: str | None = None
    value: str | None = None


class TokenTransfer(BaseModel):
    """A token (e.g., ERC-20) transfer that occurred within a transaction."""

    chain_id: str
    network: str | None = None
    tx_hash: str
    transfer_index: int
    token_address: str
    token_symbol: str | None = None
    token_name: str | None = None
    token_decimals: int | None = None
    from_address: str | None = None
    to_address: str | None = None
    value_raw: str = "0"


class Transaction(BaseModel):
    """Canonical normalized transaction, shared by all blockchains."""

    model_config = ConfigDict(from_attributes=True)

    chain_id: str
    network: str | None = None
    tx_hash: str
    block_number: int | None = None
    block_hash: str | None = None
    block_timestamp: datetime | None = None
    status: str = Field(default="confirmed", description="confirmed|pending|failed")
    transaction_type: str = Field(default="native", description="native|token_transfer|internal|other")

    # Account-based: the direct sender/recipient (denormalized for indexing).
    from_address: str | None = None
    to_address: str | None = None

    # Value in base units (see module docstring). NEVER a float.
    value: str
    value_decimals: int = 0

    fee: str | None = None
    input_data: str | None = None

    senders: list[AddressAmount] = Field(default_factory=list)
    recipients: list[AddressAmount] = Field(default_factory=list)
    token_transfers: list[TokenTransfer] = Field(default_factory=list)

    # Provenance: where and when this was fetched.
    source: str = "ethereum/etherscan"
    fetched_at: datetime

    @field_validator("tx_hash", "chain_id", "source")
    @classmethod
    def _strip_strings(cls, v: str) -> str:
        return v.strip()

    @field_validator("block_timestamp", "fetched_at", mode="before")
    @classmethod
    def _coerce_dt(cls, v: object) -> object:
        if isinstance(v, datetime):
            return as_aware_utc(v)
        return v