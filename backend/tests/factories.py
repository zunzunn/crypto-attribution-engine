"""Factories shared across tests."""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import Transaction
from app.schemas.graph import GraphEdge, TransactionGraph
from app.services.graph.builder import GraphBuilder

DEFAULT_FROM = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
DEFAULT_TO = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
DEFAULT_HASH = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

NOW = datetime.now(timezone.utc)


def make_tx(
    *,
    tx_hash: str = DEFAULT_HASH,
    chain_id: str = "ethereum",
    network: str = "mainnet",
    block_number: int = 21000000,
    block_timestamp: datetime | None = NOW,
    from_address: str = DEFAULT_FROM,
    to_address: str = DEFAULT_TO,
    value: str = "1000000000000000000",
    value_decimals: int = 18,
    status: str = "confirmed",
    input_data: str = "0x",
    fetched_at: datetime | None = None,
) -> Transaction:
    return Transaction(
        chain_id=chain_id,
        network=network,
        tx_hash=tx_hash,
        block_number=block_number,
        block_timestamp=block_timestamp,
        from_address=from_address,
        to_address=to_address,
        value=value,
        value_decimals=value_decimals,
        status=status,
        input_data=input_data,
        source="test",
        fetched_at=fetched_at or NOW,
    )


def make_two(fetched_at: datetime | None = None) -> list[Transaction]:
    return [
        make_tx(tx_hash=DEFAULT_HASH, fetched_at=fetched_at),
        make_tx(
            tx_hash="0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            value="2500000000000000000",
            fetched_at=fetched_at,
        ),
    ]


# --------------------------------------------------------------------------- #
# Phase 2 (traversal / attribution) helpers
# --------------------------------------------------------------------------- #


def eth_addr(n: int) -> str:
    """Deterministic fake Ethereum address from the integer ``n``."""
    return f"0x{n:040x}"


def tx_hash(n: int) -> str:
    """Deterministic fake transaction hash from the integer ``n``."""
    return f"0x{n:064x}"


def make_edge(
    index: int,
    from_address: str,
    to_address: str,
    *,
    chain_id: str = "ethereum",
    network: str = "mainnet",
    tx: str | None = None,
    block_number: int | None = None,
    block_timestamp: datetime | None = None,
    value: str = "1000000000000000000",
    value_decimals: int = 18,
    token_transfers: list | None = None,
) -> GraphEdge:
    return GraphEdge(
        chain_id=chain_id,
        network=network,
        tx_hash=tx or tx_hash(index),
        from_address=from_address,
        to_address=to_address,
        value=value,
        value_decimals=value_decimals,
        block_number=block_number if block_number is not None else index,
        block_timestamp=block_timestamp,
        token_transfers=token_transfers or [],
    )


def build_graph(edges: list[GraphEdge], *, chain_id: str = "ethereum", network: str = "mainnet") -> TransactionGraph:
    builder = GraphBuilder(chain_id=chain_id, network=network)
    builder.add_edges(edges)
    return builder.graph