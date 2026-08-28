"""Graph derivation tests: builder dedupe rules and DB-backed edge expansion."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models import TokenTransferRecord
from app.repositories.transaction_repo import TransactionRepository
from app.services.graph.builder import GraphBuilder
from app.services.graph.repository import DatabaseGraphExpander
from app.utils.time import as_naive_utc
from tests.factories import eth_addr, make_edge, make_tx, tx_hash

SEED = eth_addr(1)
VASP_A = eth_addr(100)
BASE = datetime(2026, 5, 1, tzinfo=timezone.utc)

REPO = TransactionRepository()
EXPANDER = DatabaseGraphExpander()


class TestGraphBuilder:
    def test_add_edge_is_idempotent(self) -> None:
        builder = GraphBuilder(chain_id="ethereum", network="mainnet")
        edge = make_edge(1, SEED, VASP_A, block_number=10, block_timestamp=BASE)
        assert builder.add_edge(edge) is True
        assert builder.add_edge(edge) is False
        assert len(builder.graph.edges) == 1

    def test_self_loop_and_missing_recipient_ignored(self) -> None:
        builder = GraphBuilder(chain_id="ethereum", network="mainnet")
        builder.add_edge(make_edge(1, SEED, SEED, block_number=1, block_timestamp=BASE))
        builder.add_edge(make_edge(2, SEED, "", block_number=2, block_timestamp=BASE))
        assert builder.graph.edges == []

    def test_different_transfers_create_separate_edges(self) -> None:
        builder = GraphBuilder(chain_id="ethereum", network="mainnet")
        builder.add_edge(make_edge(1, SEED, VASP_A, block_number=10, block_timestamp=BASE))
        builder.add_edge(make_edge(1, SEED, eth_addr(2), block_number=11, block_timestamp=BASE))
        assert len(builder.graph.edges) == 2
        assert len(builder.graph.nodes) == 3

    def test_same_transfer_two_edges_keeps_first(self) -> None:
        builder = GraphBuilder(chain_id="ethereum", network="mainnet")
        first = make_edge(1, SEED, VASP_A, block_number=10, block_timestamp=BASE)
        builder.add_edge(first)
        builder.add_edge(first.model_copy(update={"value": "999"}))
        assert len(builder.graph.edges) == 1
        assert builder.graph.edges[0].value == first.value


class TestDatabaseGraphExpander:
    async def test_outgoing_edges_for_confirmed_only(self, session) -> None:
        await REPO.upsert_many(
            session,
            [
                make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                        from_address=SEED, to_address=VASP_A),
                make_tx(tx_hash=tx_hash(2), block_number=11, block_timestamp=BASE,
                        from_address=SEED, to_address=eth_addr(2), status="failed"),
            ],
        )
        edges = await EXPANDER.outgoing(
            session, chain_id="ethereum", network="mainnet", address=SEED
        )
        assert [e.tx_hash for e in edges] == [tx_hash(1)]

    async def test_contract_creation_skipped(self, session) -> None:
        tx = make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                     from_address=SEED, to_address=None)
        await REPO.upsert_many(session, [tx])
        edges = await EXPANDER.outgoing(
            session, chain_id="ethereum", network="mainnet", address=SEED
        )
        assert edges == []

    async def test_tokens_attached_as_edge_evidence(self, session) -> None:
        await REPO.upsert_many(
            session,
            [make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                     from_address=SEED, to_address=VASP_A)],
        )
        session.add(
            TokenTransferRecord(
                chain_id="ethereum", network="mainnet", tx_hash=tx_hash(1), transfer_index=0,
                token_address=eth_addr(900), token_symbol="USDT", token_decimals=6,
                from_address=SEED, to_address=VASP_A, value_raw="1000000",
                source="test", fetched_at=as_naive_utc(BASE),
            )
        )
        await session.flush()

        edges = await EXPANDER.outgoing(
            session, chain_id="ethereum", network="mainnet", address=SEED
        )
        assert len(edges) == 1
        assert edges[0].token_transfers[0].token_symbol == "USDT"
        assert edges[0].value_decimals == 18

    async def test_network_filter(self, session) -> None:
        await REPO.upsert_many(
            session,
            [
                make_tx(tx_hash=tx_hash(1), block_number=10, block_timestamp=BASE,
                        from_address=SEED, to_address=VASP_A, network="mainnet"),
                make_tx(tx_hash=tx_hash(2), block_number=11, block_timestamp=BASE,
                        from_address=SEED, to_address=eth_addr(2), network="sepolia"),
            ],
        )
        edges = await EXPANDER.outgoing(
            session, chain_id="ethereum", network="mainnet", address=SEED
        )
        assert [e.tx_hash for e in edges] == [tx_hash(1)]

    async def test_unknown_address_has_no_edges(self, session) -> None:
        edges = await EXPANDER.outgoing(
            session, chain_id="ethereum", network="mainnet", address=eth_addr(999)
        )
        assert edges == []