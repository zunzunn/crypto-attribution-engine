"""Graph domain schemas: nodes, edges, and the directed transaction graph.

An edge is a directed fund movement between two wallet addresses derived from a
normalized transaction. It carries enough evidence to trace back to the
original transaction: chain/network, tx hash, sender, recipient, base-unit
value, timestamp, fee, and any token transfers that occurred inside the same
transaction.

These schemas double as the internal domain models used by the graph builder,
the traversal engine, and the attribution service (one model set, no
duplication). The ``value`` fields are base-unit integer strings (never
floats), matching the canonical transaction schema.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.transaction import TokenTransfer


class GraphNode(BaseModel):
    """A wallet address participating in the explored subgraph."""

    model_config = ConfigDict(frozen=True)

    address: str
    chain_id: str
    network: str | None = None
    first_seen_at: datetime | None = None


class GraphEdge(BaseModel):
    """A directed transfer between two addresses, rooted in one transaction.

    ``value`` is the native-asset amount in base units (base-unit string, same
    exponent as the canonical ``Transaction.value``). If the transaction also
    moved tokens, those transfers are attached via ``token_transfers`` as
    additional evidence (they are not expanded as separate edges in forward
    traversal).
    """

    model_config = ConfigDict(frozen=True)

    chain_id: str
    network: str | None = None
    tx_hash: str
    from_address: str
    to_address: str
    value: str = "0"
    value_decimals: int = 0
    block_number: int | None = None
    block_timestamp: datetime | None = None
    fee: str | None = None
    transaction_type: str = "native"
    token_transfers: list[TokenTransfer] = Field(default_factory=list)


class TransactionGraph(BaseModel):
    """A directed graph (nodes + edges) for a single chain/network window.

    Addresses are the nodes; ``edges`` is a flat list (insertion order is the
    discovery/derivation order and is deliberately deterministic). Adjacency is
    exposed via the ``outgoing``/``incoming`` helpers rather than a mutable
    adjacency structure so the model stays serializable and immutable-safe.
    """

    chain_id: str
    network: str | None = None
    nodes: dict[str, GraphNode] = Field(default_factory=dict)
    edges: list[GraphEdge] = Field(default_factory=list)

    def outgoing(self, address: str) -> list[GraphEdge]:
        """Edges leaving ``address`` (forward flow direction)."""
        return [e for e in self.edges if e.from_address == address]

    def incoming(self, address: str) -> list[GraphEdge]:
        """Edges arriving at ``address`` (useful as attribution evidence)."""
        return [e for e in self.edges if e.to_address == address]