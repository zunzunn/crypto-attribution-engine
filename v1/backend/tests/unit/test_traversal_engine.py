"""Traversal engine unit tests (pure domain logic, in-memory expander only).

Deterministic fixtures: edges are fabricated addresses/timestamps, never live
chain data. Covers forward BFS behavior, hop limits, time window, min value,
fan-out/global caps, cycle handling, duplicate edges, and determinism.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.graph import GraphNode, TransactionGraph
from app.schemas.traversal import TraversalRequest
from app.services.graph.repository import InMemoryGraphExpander
from app.services.traversal.engine import TraversalEngine
from tests.factories import build_graph, eth_addr, make_edge

SEED = eth_addr(1)
A = eth_addr(2)
B = eth_addr(3)
C = eth_addr(4)

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def expander(edges):
    return InMemoryGraphExpander(build_graph(edges))


def graph_expander(graph: TransactionGraph):
    return InMemoryGraphExpander(graph)


async def run(edges, **kwargs):
    request = TraversalRequest(
        chain_id="ethereum",
        network="mainnet",
        seed_address=SEED,
        **kwargs,
    )
    ex = expander(edges)
    engine = TraversalEngine()
    return await engine.traverse(
        request=request,
        expand=lambda addr: ex.outgoing(None, chain_id="ethereum", network="mainnet", address=addr),
    )


async def run_graph(graph: TransactionGraph, **kwargs):
    request = TraversalRequest(
        chain_id="ethereum",
        network="mainnet",
        seed_address=SEED,
        **kwargs,
    )
    ex = graph_expander(graph)
    engine = TraversalEngine()
    return await engine.traverse(
        request=request,
        expand=lambda addr: ex.outgoing(None, chain_id="ethereum", network="mainnet", address=addr),
    )


def raw_graph(edges):
    """A TransactionGraph built WITHOUT the builder's dedupe/self-loop filters."""
    return TransactionGraph(
        chain_id="ethereum",
        network="mainnet",
        nodes={
            e.from_address: GraphNode(address=e.from_address, chain_id="ethereum", network="mainnet")
            for e in edges
        },
        edges=edges,
    )


class TestBasicForward:
    async def test_discovers_path_chain(self) -> None:
        edges = [
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, A, B, block_timestamp=T0 + timedelta(days=1), block_number=20),
            make_edge(3, B, C, block_timestamp=T0 + timedelta(days=2), block_number=30),
        ]
        result = await run(edges, max_hops=3)
        assert result.addresses_discovered == 3
        assert result.discovered_addresses == [A, B, C]
        paths = {p.target_address: p for p in result.paths}
        assert [h.edge.tx_hash for h in paths[A].hops] == [edges[0].tx_hash]
        assert len(paths[B].hops) == 2
        assert len(paths[C].hops) == 3
        assert result.seed_address == SEED

    async def test_paths_preserve_full_evidence(self) -> None:
        edges = [
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, A, B, block_timestamp=T0 + timedelta(days=1), block_number=20),
        ]
        result = await run(edges, max_hops=3)
        path = next(p for p in result.paths if p.target_address == B)
        hops = path.hops
        assert [h.edge.from_address for h in hops] == [SEED, A]
        assert [h.edge.to_address for h in hops] == [A, B]
        for i, h in enumerate(hops, start=1):
            assert h.step == i

    async def test_empty_graph_no_discovery(self) -> None:
        result = await run([], max_hops=3)
        assert result.paths == []
        assert result.discovered_addresses == []
        assert result.edges_examined == 0


class TestMaxHops:
    async def test_max_hops_truncates_expansion(self) -> None:
        edges = [
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, A, B, block_timestamp=T0 + timedelta(days=1), block_number=20),
        ]
        result = await run(edges, max_hops=1)
        assert result.discovered_addresses == [A]
        assert result.edges_examined == 1

    async def test_max_hops_does_not_expand_boundary(self) -> None:
        edges = [
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, A, B, block_timestamp=T0 + timedelta(days=1), block_number=20),
            make_edge(3, B, C, block_timestamp=T0 + timedelta(days=2), block_number=30),
        ]
        result = await run(edges, max_hops=2)
        assert result.discovered_addresses == [A, B]
        assert C not in result.discovered_addresses

    async def test_max_hops_rejects_out_of_range(self) -> None:
        with pytest.raises(ValueError):
            TraversalRequest(chain_id="ethereum", seed_address=SEED, max_hops=0)
        with pytest.raises(ValueError):
            TraversalRequest(chain_id="ethereum", seed_address=SEED, max_hops=21)


class TestTimeWindow:
    def _clock_edges(self) -> list:
        return [
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, A, B, block_timestamp=T0 + timedelta(days=1), block_number=20),
            make_edge(3, SEED, C, block_timestamp=T0 + timedelta(days=5), block_number=11),
        ]

    async def test_time_from_prunes_early_edges(self) -> None:
        result = await run(self._clock_edges(), max_hops=2, time_from=T0 + timedelta(days=2))
        assert A not in result.discovered_addresses
        assert C in result.discovered_addresses
        assert result.pruned_by_reason.get("time_window") == 1

    async def test_time_to_prunes_late_edges(self) -> None:
        result = await run(self._clock_edges(), max_hops=2, time_to=T0 + timedelta(hours=1))
        assert A in result.discovered_addresses
        assert C not in result.discovered_addresses
        # Both A->B (day 1) and SEED->C (day 5) fall after the window.
        assert result.pruned_by_reason.get("time_window") == 2
        # B is never reachable because A's mid path also lies at day 1 (> time_to window edge is A->B).
        assert B not in result.discovered_addresses

    async def test_none_timestamp_survives_window(self) -> None:
        edges = [
            make_edge(1, SEED, A, block_timestamp=None, block_number=10),
        ]
        result = await run(edges, max_hops=1, time_from=T0, time_to=T0 + timedelta(days=1))
        assert A in result.discovered_addresses

    async def test_invalid_window_rejected(self) -> None:
        with pytest.raises(ValueError):
            TraversalRequest(
                chain_id="ethereum",
                seed_address=SEED,
                time_from=T0 + timedelta(days=2),
                time_to=T0,
            )


class TestMinValue:
    async def test_min_value_prunes_dust(self) -> None:
        edges = [
            make_edge(1, SEED, A, value="1000", block_timestamp=T0, block_number=10),
            make_edge(2, SEED, B, value="5000000", block_timestamp=T0, block_number=11),
        ]
        result = await run(edges, max_hops=1, min_value="1000000")
        assert A not in result.discovered_addresses
        assert B in result.discovered_addresses
        assert result.pruned_by_reason.get("value_below_threshold") == 1

    async def test_min_value_equal_is_kept(self) -> None:
        edges = [make_edge(1, SEED, A, value="1000000", block_timestamp=T0, block_number=10)]
        result = await run(edges, max_hops=1, min_value="1000000")
        assert A in result.discovered_addresses


class TestCaps:
    async def test_max_edges_per_hop_keeps_earliest(self) -> None:
        edges = [
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, SEED, B, block_timestamp=T0 + timedelta(hours=1), block_number=11),
            make_edge(3, SEED, C, block_timestamp=T0 + timedelta(hours=2), block_number=12),
        ]
        result = await run(edges, max_hops=1, max_edges_per_hop=2)
        assert result.discovered_addresses == [A, B]
        assert result.pruned_by_reason.get("max_edges_per_hop") == 1

    async def test_max_total_edges_global_cap(self) -> None:
        edges = [
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, A, B, block_timestamp=T0 + timedelta(days=1), block_number=20),
            make_edge(3, B, C, block_timestamp=T0 + timedelta(days=2), block_number=30),
        ]
        result = await run(edges, max_hops=3, max_total_edges=1)
        assert result.discovered_addresses == [A]
        assert result.pruned_by_reason.get("max_total_edges") == 1


class TestCyclesAndRevisits:
    async def test_back_edge_to_visited_is_cycle(self) -> None:
        edges = [
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, A, B, block_timestamp=T0 + timedelta(days=1), block_number=20),
            make_edge(3, B, A, block_timestamp=T0 + timedelta(days=2), block_number=30),
        ]
        result = await run(edges, max_hops=4)
        assert result.discovered_addresses == [A, B]
        assert result.cycles_encountered == 1
        assert result.pruned_by_reason.get("cycle") == 1
        # The traversal terminates - no infinite expansion.
        assert result.paths

    async def test_self_loop_on_frontier_is_cycle(self) -> None:
        # Edge A->A bypasses the graph builder's own filter, so the engine's
        # self-loop guard must catch it as a cycle.
        graph = raw_graph([
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, A, A, block_timestamp=T0 + timedelta(days=1), block_number=20),
        ])
        result = await run_graph(graph, max_hops=2)
        assert result.discovered_addresses == [A]
        assert result.cycles_encountered == 1
        assert result.pruned_by_reason.get("cycle") == 1

    async def test_revisit_via_other_path_keeps_shortest_path(self) -> None:
        X = eth_addr(5)
        edges = [
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, SEED, X, block_timestamp=T0, block_number=11),
            make_edge(3, A, X, block_timestamp=T0 + timedelta(days=1), block_number=20),
        ]
        result = await run(edges, max_hops=3)
        path = next(p for p in result.paths if p.target_address == X)
        assert path.hop_count == 1  # shortest path (seed -> X) kept
        assert result.pruned_by_reason.get("already_visited") == 1

    async def test_duplicate_edges_produce_single_path(self) -> None:
        # build_graph dedupes identical (tx_hash, from, to) edges before the
        # engine sees them, so a single path with one incoming edge is produced.
        dup = make_edge(1, SEED, A, block_timestamp=T0, block_number=10)
        edges = [dup, dup.model_copy()]
        result = await run(edges, max_hops=1)
        assert result.discovered_addresses == [A]
        path = next(p for p in result.paths if p.target_address == A)
        assert path.hop_count == 1
        assert len(result.node_incoming_edges[A]) == 1  # deduped at graph build
        assert result.edges_examined == 1


class TestDeterminism:
    async def test_out_of_order_input_is_processed_in_order(self) -> None:
        # Edges supplied newest-first; engine must process (block,txHash) ascent.
        edges = [
            make_edge(3, SEED, C, block_timestamp=T0 + timedelta(hours=2), block_number=13),
            make_edge(1, SEED, A, block_timestamp=T0, block_number=11),
            make_edge(2, SEED, B, block_timestamp=T0 + timedelta(hours=1), block_number=12),
        ]
        result = await run(edges, max_hops=1, max_edges_per_hop=3)
        assert result.discovered_addresses == [A, B, C]

    async def test_two_runs_identical_results(self) -> None:
        edges = [
            make_edge(1, SEED, A, block_timestamp=T0, block_number=10),
            make_edge(2, A, B, block_timestamp=T0 + timedelta(days=1), block_number=20),
            make_edge(3, SEED, C, block_timestamp=T0 + timedelta(days=3), block_number=12),
        ]
        first = await run(edges, max_hops=3)
        second = await run(edges, max_hops=3)
        assert first.model_dump() == second.model_dump()