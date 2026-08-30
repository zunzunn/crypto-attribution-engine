"""Incremental graph builder.

Turns normalized transactions (already persisted in PostgreSQL) into the
directed ``TransactionGraph`` used by traversal. Nodes are wallet addresses;
edges are address-to-address fund movements carrying full tx evidence. The
builder is idempotent: the same (tx_hash, from, to) transfer is never emitted
twice, so duplicate rows collapse into a single edge.
"""

from __future__ import annotations

from datetime import datetime

from app.schemas.graph import GraphEdge, GraphNode, TransactionGraph


class GraphBuilder:
    def __init__(self, *, chain_id: str, network: str | None = None) -> None:
        self.graph = TransactionGraph(chain_id=chain_id, network=network)
        self._present_keys: set[tuple[str, str, str]] = set()

    def add_node(self, address: str, *, seen_at: datetime | None = None) -> GraphNode:
        node = self.graph.nodes.get(address)
        if node is None:
            node = GraphNode(
                address=address,
                chain_id=self.graph.chain_id,
                network=self.graph.network,
                first_seen_at=seen_at,
            )
            self.graph.nodes[address] = node
        return node

    def add_edge(self, edge: GraphEdge) -> bool:
        """Add ``edge`` unless an identical (tx_hash, from, to) exists.

        Returns True when a new edge was actually inserted. Self-loops
        (from == to) and edges without a recipient are ignored here; the
        traversal engine additionally guards against revisiting addresses.
        """
        if not edge.to_address or edge.from_address == edge.to_address:
            return False
        key = (edge.tx_hash, edge.from_address, edge.to_address)
        if key in self._present_keys:
            return False
        self._present_keys.add(key)
        self.graph.edges.append(edge)
        self.add_node(edge.from_address, seen_at=edge.block_timestamp)
        self.add_node(edge.to_address, seen_at=edge.block_timestamp)
        return True

    def add_edges(self, edges: list[GraphEdge]) -> int:
        added = 0
        for edge in edges:
            if self.add_edge(edge):
                added += 1
        return added