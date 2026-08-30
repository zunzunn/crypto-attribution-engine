"""Tests for the dev-only demo seeding mechanism.

Covers determinism (fixtures match the shared test-factory convention),
idempotent seeding, end-to-end attribution over the seeded graph, and a
surgical reset that only touches demo-owned rows.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

import app.models  # noqa: F401  (register models on metadata)
from app.db.base import Base
from app.dev import demo_data
from app.dev.seed_demo import reset_demo, seed_demo
from app.models import EntityAddressRecord, EntityRecord, TransactionRecord
from app.repositories.transaction_repo import TransactionRepository
from app.schemas import EntityType, TraversalRequest
from app.services.attribution.registry import DatabaseAddressRegistry
from app.services.attribution.scoring import ConfidenceScorer
from app.services.attribution.service import AttributionService
from app.services.graph.repository import DatabaseGraphExpander
from app.services.traversal.engine import TraversalEngine
from tests.factories import eth_addr, make_tx, tx_hash


def build_sqlite_factory():
    from app.db.engine import build_session_factory

    factory = build_session_factory("sqlite+aiosqlite:///:memory:")
    return factory


class TestDemoDataDeterminism:
    def test_addresses_match_factory_convention(self) -> None:
        assert demo_data.SEED == eth_addr(1)
        assert demo_data.INTER == eth_addr(4)
        assert demo_data.VASP_A == eth_addr(100)

    def test_hashes_match_factory_convention(self) -> None:
        assert demo_data.SEED_TO_INTER_TX == tx_hash(1)
        assert demo_data.INTER_TO_VASP_TX == tx_hash(2)

    def test_build_transactions_is_deterministic(self) -> None:
        first = demo_data.build_transactions()
        second = demo_data.build_transactions()
        assert first == second
        assert len(first) == 2

        hop1, hop2 = first
        assert (hop1.from_address, hop1.to_address) == (demo_data.SEED, demo_data.INTER)
        assert (hop2.from_address, hop2.to_address) == (demo_data.INTER, demo_data.VASP_A)
        assert hop1.tx_hash == tx_hash(1) and hop2.tx_hash == tx_hash(2)
        assert hop1.block_number == 10 and hop2.block_number == 20
        assert hop2.block_timestamp > hop1.block_timestamp
        assert all(tx.source == "demo_fixture" for tx in first)

    def test_entity_is_clearly_synthetic(self) -> None:
        assert demo_data.VASP_A_NAME == "Candidate VASP alpha"
        assert demo_data.VASP_A_TAG_SOURCE == "demo_fixture_v1"
        assert demo_data.VASP_A_ENTITY_CATEGORY == EntityType.VASP
        assert demo_data.VASP_A.startswith("0x00000000000000000000")


class TestSeedDemo:
    @pytest.fixture
    async def demo_factory(self):
        factory = build_sqlite_factory()
        async with factory.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield factory
        await factory.dispose()

    async def _tx_count(self, session, *, exclude: set[str] | None = None) -> int:
        stmt = select(func.count()).select_from(TransactionRecord)
        if exclude:
            stmt = stmt.where(TransactionRecord.tx_hash.notin_(exclude))
        return int((await session.execute(stmt)).scalar_one())

    async def test_seed_is_idempotent(self, demo_factory) -> None:
        first = await seed_demo(demo_factory)
        assert first.inserted == 2
        assert first.skipped == 0
        assert first.entity_name == "Candidate VASP alpha"
        assert first.entity_tag_source == "demo_fixture_v1"

        second = await seed_demo(demo_factory)
        assert second.inserted == 0
        assert second.skipped == 2

        async with demo_factory() as session:
            tx_count = await self._tx_count(session)
            entity_count = int(
                (await session.execute(select(func.count()).select_from(EntityRecord))).scalar_one()
            )
            link_count = int(
                (await session.execute(select(func.count()).select_from(EntityAddressRecord))).scalar_one()
            )
        assert tx_count == 2
        assert entity_count == 1
        assert link_count == 1

    async def test_seeded_graph_attributes_end_to_end(self, demo_factory) -> None:
        await seed_demo(demo_factory)
        service = AttributionService(
            engine=TraversalEngine(),
            expander=DatabaseGraphExpander(),
            registry=DatabaseAddressRegistry(),
            scorer=ConfidenceScorer(),
        )
        async with demo_factory() as session:
            response = await service.investigate(
                session,
                TraversalRequest(
                    chain_id=demo_data.DEMO_CHAIN,
                    network=demo_data.DEMO_NETWORK,
                    seed_address=demo_data.SEED,
                    max_hops=3,
                ),
            )
        assert len(response.candidates) == 1
        candidate = response.candidates[0]
        assert candidate.matched_address == demo_data.VASP_A
        assert candidate.entity.name == "Candidate VASP alpha"
        assert candidate.hop_count == 2
        # Full path evidence is preserved hop-by-hop; the incoming support edge
        # against VASP_A is the INTER -> VASP_A transfer.
        assert [hop.edge.tx_hash for hop in candidate.path.hops] == [
            demo_data.SEED_TO_INTER_TX,
            demo_data.INTER_TO_VASP_TX,
        ]
        assert candidate.evidence_tx_hashes == [demo_data.INTER_TO_VASP_TX]

    async def test_reset_only_removes_demo_rows(self, demo_factory) -> None:
        await seed_demo(demo_factory)

        async with demo_factory() as session:
            await TransactionRepository().upsert_many(
                session,
                [
                    make_tx(
                        tx_hash=tx_hash(7), block_number=70, from_address=eth_addr(900),
                        to_address=eth_addr(901),
                        block_timestamp=datetime(2026, 6, 1, tzinfo=timezone.utc),
                    )
                ],
            )
            await session.flush()
            await DatabaseAddressRegistry().register(
                session, chain_id="ethereum", network="mainnet", address=eth_addr(300),
                category=EntityType.BRIDGE, name="Other kept entity",
                tag_source="operator_curated_v2", tag_version="v2",
            )
            await session.commit()

        result = await reset_demo(demo_factory)
        assert result.transactions_deleted == 2
        assert result.address_links_deleted == 1
        assert result.entities_deleted == 1

        async with demo_factory() as session:
            assert await self._tx_count(session, exclude=demo_data.demo_tx_hashes()) == 1
            tags = set(
                (await session.execute(select(EntityRecord.tag_source))).scalars().all()
            )
            assert tags == {"operator_curated_v2"}
            links = (
                (await session.execute(select(EntityAddressRecord.address))).scalars().all()
            )
            assert links == [eth_addr(300)]

        # Reset is itself idempotent / safe to re-run.
        again = await reset_demo(demo_factory)
        assert again.transactions_deleted == 0
        assert again.address_links_deleted == 0
        assert again.entities_deleted == 0