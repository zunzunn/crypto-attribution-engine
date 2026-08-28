"""Traversal schemas: request parameters, evidence hops/paths, results.

``TraversalRequest`` drives the bounded BFS. ``min_value`` is expressed in the
chain's base units (same exponent as stored values), so filtering never touches
floating point. When ``network`` is omitted the traversal spans all networks of
the chain; every evidence edge still carries its own network so results remain
traceable.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.graph import GraphEdge


class TraversalRequest(BaseModel):
    chain_id: str = Field(default="ethereum", description="Chain id, e.g. 'ethereum'")
    network: str | None = Field(
        default=None,
        description="Network filter (e.g. 'mainnet'). None spans all networks of the chain.",
    )
    seed_address: str = Field(description="Suspect wallet address to trace from")
    direction: Literal["forward"] = Field(default="forward", description="Only 'forward' now")
    max_hops: int = Field(default=3, ge=1, le=20, description="Max BFS hop depth")
    time_from: datetime | None = Field(default=None, description="Only follow txs at/after this time")
    time_to: datetime | None = Field(default=None, description="Only follow txs at/before this time")
    min_value: str | None = Field(
        default=None,
        description="Minimum native value in base units (same exponent as stored txs); dust filter.",
    )
    max_edges_per_hop: int = Field(default=50, ge=1, le=5000, description="Fan-out cap per address")
    max_total_edges: int = Field(
        default=500, ge=1, le=100000, description="Global cap on evidence edges kept"
    )

    @model_validator(mode="after")
    def _time_window_ordered(self) -> TraversalRequest:
        if self.time_from and self.time_to and self.time_from > self.time_to:
            raise ValueError("time_from must not be later than time_to")
        return self


class EvidenceHop(BaseModel):
    """One edge on an evidence path; step is 1-based hop number from the seed."""

    step: int
    edge: GraphEdge


class EvidencePath(BaseModel):
    """The complete evidence path from the seed to one discovered address.

    A path preserves every intermediate transaction so an investigator can
    re-derive the fund flow hop by hop instead of only seeing the final wallet.
    """

    seed_address: str
    target_address: str
    hops: list[EvidenceHop] = Field(default_factory=list)
    hop_count: int = Field(default=0)
    cycle_detected: bool = Field(
        default=False,
        description="True if the path would revisit an address (defensive; BFS keeps paths simple).",
    )


class TraversalResult(BaseModel):
    """Deterministic output of one bounded BFS traversal."""

    chain_id: str
    network: str | None = None
    seed_address: str
    max_hops: int
    paths: list[EvidencePath] = Field(default_factory=list)
    discovered_addresses: list[str] = Field(default_factory=list)
    edges_examined: int = Field(default=0)
    addresses_discovered: int = Field(default=0)
    cycles_encountered: int = Field(default=0)
    total_pruned_edges: int = Field(default=0)
    pruned_by_reason: dict[str, int] = Field(default_factory=dict)
    node_incoming_edges: dict[str, list[GraphEdge]] = Field(
        default_factory=dict,
        description="All non-pruned edges arriving at each discovered address (corroboration evidence).",
    )