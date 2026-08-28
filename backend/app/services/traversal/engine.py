"""Bounded BFS traversal over the derived transaction graph.

The engine is pure traversal logic: given a seed address and an async
``expand(address)`` callable, it performs a breadth-first forward walk bounded
by ``TraversalRequest`` constraints. Expansion I/O (database, in-memory graph)
is injected so the engine is deterministic and unit-testable.

Guarantees
----------
* Deterministic: edges are processed in a stable (block, tx_hash, recipient)
  order per address, BFS queue order is FIFO, and output lists are sorted.
* Bounded: ``max_hops``, ``time_from``/``time_to``, ``min_value``,
  ``max_edges_per_hop`` and ``max_total_edges`` all prune the frontier.
* Cycle-safe: every expanded address is recorded in a global visited set, and
  edges pointing back into the current path (incl. self-loops) are counted as
  cycles and never re-expanded.
* Evidence-preserving: each discovered address keeps its complete (shortest)
  seed-to-address path plus every non-pruned incoming edge, so attributions are
  fully traceable rather than just 'the final wallet'.
"""

from __future__ import annotations

from collections import Counter, deque
from collections.abc import Awaitable, Callable

from app.schemas.graph import GraphEdge
from app.schemas.traversal import (
    EvidenceHop,
    EvidencePath,
    TraversalRequest,
    TraversalResult,
)

ExpandFn = Callable[[str], Awaitable[list[GraphEdge]]]


def _base_int(value: str) -> int | None:
    """Parse a base-unit integer string; None when not an integer."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _sort_key(edge: GraphEdge) -> tuple:
    ts = edge.block_timestamp
    epoch = int(ts.timestamp()) if ts else -1
    return (epoch, edge.block_number if edge.block_number is not None else -1, edge.tx_hash, edge.to_address or "")


def _path_addresses(path: list[GraphEdge], seed: str) -> set[str]:
    addrs = {seed}
    for edge in path:
        addrs.add(edge.from_address)
        addrs.add(edge.to_address or "")
    addrs.discard("")
    return addrs


class TraversalEngine:
    def __init__(self) -> None:
        pass

    async def traverse(
        self,
        *,
        request: TraversalRequest,
        expand: ExpandFn,
    ) -> TraversalResult:
        if request.direction != "forward":
            raise ValueError(f"unsupported direction: {request.direction}")

        seed = request.seed_address
        visited: set[str] = {seed}
        paths: dict[str, list[GraphEdge]] = {seed: []}
        incoming_edges: dict[str, list[GraphEdge]] = {}
        queue: deque[tuple[str, int]] = deque([(seed, 0)])

        pruned: Counter[str] = Counter()
        edges_examined = 0
        cycles_encountered = 0

        while queue:
            address, depth = queue.popleft()

            if depth >= request.max_hops:
                continue

            outgoing = await expand(address)
            edges_examined += len(outgoing)
            survivors: list[GraphEdge] = []

            for edge in sorted(outgoing, key=_sort_key):
                target = edge.to_address

                if not target:
                    pruned["untraceable_edge"] += 1
                    continue
                if target == address:
                    pruned["cycle"] += 1
                    cycles_encountered += 1
                    continue

                ts = edge.block_timestamp
                if request.time_from and ts and ts < request.time_from:
                    pruned["time_window"] += 1
                    continue
                if request.time_to and ts and ts > request.time_to:
                    pruned["time_window"] += 1
                    continue

                if request.min_value is not None:
                    floor = _base_int(request.min_value)
                    amount = _base_int(edge.value)
                    if floor is not None and amount is not None and amount < floor:
                        pruned["value_below_threshold"] += 1
                        continue

                survivors.append(edge)

            if len(survivors) > request.max_edges_per_hop:
                pruned["max_edges_per_hop"] += len(survivors) - request.max_edges_per_hop
                survivors = survivors[: request.max_edges_per_hop]

            for edge in survivors:
                target = edge.to_address or ""
                if len(paths) - 1 >= request.max_total_edges:
                    pruned["max_total_edges"] += 1
                    continue

                incoming_edges.setdefault(target, []).append(edge)

                if target in visited:
                    if target in _path_addresses(paths[address], seed):
                        pruned["cycle"] += 1
                        cycles_encountered += 1
                    else:
                        pruned["already_visited"] += 1
                    continue

                paths[target] = paths[address] + [edge]
                visited.add(target)
                queue.append((target, depth + 1))

        discovered = sorted(addr for addr in visited if addr != seed)

        result_paths: list[EvidencePath] = []
        for address in discovered:
            edge_path = paths[address]
            result_paths.append(
                EvidencePath(
                    seed_address=seed,
                    target_address=address,
                    hops=[
                        EvidenceHop(step=step, edge=edge)
                        for step, edge in enumerate(edge_path, start=1)
                    ],
                    hop_count=len(edge_path),
                    cycle_detected=False,
                )
            )
        result_paths.sort(key=lambda p: (p.hop_count, p.target_address))

        return TraversalResult(
            chain_id=request.chain_id,
            network=request.network,
            seed_address=seed,
            max_hops=request.max_hops,
            paths=result_paths,
            discovered_addresses=discovered,
            edges_examined=edges_examined,
            addresses_discovered=len(discovered),
            cycles_encountered=cycles_encountered,
            total_pruned_edges=sum(pruned.values()),
            pruned_by_reason=dict(sorted(pruned.items())),
            node_incoming_edges={address: incoming_edges.get(address, []) for address in discovered},
        )