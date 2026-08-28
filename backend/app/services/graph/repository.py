"""Graph data access + expansion protocols.

``DatabaseGraphExpander`` loads outgoing edges (confirmed native transactions
plus their token transfers) for one address directly from PostgreSQL. This is
the "derive-a-directed-graph-from-persisted-transactions" entry point: edges are
materialized on demand as BFS progresses, bounded by the traversal parameters.

``InMemoryGraphExpander`` renders the same interface from a static
``TransactionGraph`` so the traversal engine is unit-testable without a
database or any network call.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import IngestionError
from app.models import TokenTransferRecord, TransactionRecord
from app.schemas.graph import GraphEdge, TransactionGraph
from app.schemas.transaction import TokenTransfer
from app.utils.time import as_aware_utc


class GraphExpander(Protocol):
    """Anything that can answer 'which edges leave this address?'."""

    async def outgoing(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        network: str | None,
        address: str,
    ) -> list[GraphEdge]:
        ...


def _token_record_to_schema(row: TokenTransferRecord) -> TokenTransfer:
    return TokenTransfer(
        chain_id=row.chain_id,
        network=row.network,
        tx_hash=row.tx_hash,
        transfer_index=row.transfer_index,
        token_address=row.token_address,
        token_symbol=row.token_symbol,
        token_name=row.token_name,
        token_decimals=row.token_decimals,
        from_address=row.from_address,
        to_address=row.to_address,
        value_raw=row.value_raw,
    )


def _transaction_to_edge(row: TransactionRecord) -> GraphEdge:
    if not row.to_address or row.from_address == row.to_address:
        raise IngestionError(f"unexpected non-edge row for tx {row.tx_hash}")
    return GraphEdge(
        chain_id=row.chain_id,
        network=row.network,
        tx_hash=row.tx_hash,
        from_address=row.from_address,
        to_address=row.to_address,
        value=row.value,
        value_decimals=row.value_decimals,
        block_number=row.block_number,
        block_timestamp=as_aware_utc(row.block_timestamp),
        fee=row.fee,
        transaction_type=row.transaction_type,
        token_transfers=[],
    )


class DatabaseGraphExpander:
    """Loads outgoing edges for an address from the ``transactions`` table.

    Only confirmed transactions are traversed (failed txs are not evidence of a
    completed fund movement). Contract-creations and self-loops are dropped.
    Token transfers are attached as edge evidence, keyed by tx hash.
    """

    async def outgoing(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        network: str | None,
        address: str,
    ) -> list[GraphEdge]:
        stmt = (
            select(TransactionRecord)
            .where(
                TransactionRecord.chain_id == chain_id,
                TransactionRecord.from_address == address,
                TransactionRecord.status == "confirmed",
            )
            .order_by(
                TransactionRecord.block_number.asc(),
                TransactionRecord.tx_hash.asc(),
            )
        )
        if network:
            stmt = stmt.where(TransactionRecord.network == network)

        rows = list((await session.execute(stmt)).scalars())

        edges: list[GraphEdge] = []
        edgeable = [r for r in rows if r.to_address and r.from_address != r.to_address]
        if edgeable:
            hashes = {r.tx_hash for r in edgeable}
            tt_stmt = select(TokenTransferRecord).where(
                TokenTransferRecord.chain_id == chain_id,
                TokenTransferRecord.tx_hash.in_(hashes),
            )
            if network:
                tt_stmt = tt_stmt.where(TokenTransferRecord.network == network)
            tt_by_hash: dict[str, list[TokenTransfer]] = {}
            for tt in (await session.execute(tt_stmt)).scalars():
                tt_by_hash.setdefault(tt.tx_hash, []).append(_token_record_to_schema(tt))

        for row in rows:
            try:
                edge = _transaction_to_edge(row)
            except IngestionError:
                continue
            edge = edge.model_copy(update={"token_transfers": tt_by_hash.get(row.tx_hash, [])})
            edges.append(edge)
        return edges


class InMemoryGraphExpander:
    """Test/demo expander serving outgoing edges from a static graph."""

    def __init__(self, graph: TransactionGraph) -> None:
        self._graph = graph

    @property
    def graph(self) -> TransactionGraph:
        return self._graph

    async def outgoing(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        network: str | None,
        address: str,
    ) -> list[GraphEdge]:
        edges = [e for e in self._graph.edges if e.from_address == address]
        if chain_id != self._graph.chain_id:
            return []
        if network and network != self._graph.network:
            return []
        return edges