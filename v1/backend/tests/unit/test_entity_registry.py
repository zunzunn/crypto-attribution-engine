"""Database-backed entity registry tests (local, deterministic)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select

from app.models import EntityAddressRecord, EntityRecord
from app.schemas import EntityType
from app.services.attribution.registry import DatabaseAddressRegistry
from tests.factories import eth_addr

REGISTRY = DatabaseAddressRegistry()

VASP_A = eth_addr(100)
VASP_B = eth_addr(101)
MIXER = eth_addr(200)

NOW = datetime.now(timezone.utc)


class TestRegister:
    async def test_register_and_lookup(self, session) -> None:
        await REGISTRY.register(
            session,
            chain_id="ethereum",
            network="mainnet",
            address=VASP_A,
            category=EntityType.VASP,
            name="Candidate VASP alpha",
            tag_source="fixture_list_v1",
            tag_version="v1",
        )
        match = await REGISTRY.lookup(
            session, chain_id="ethereum", network="mainnet", address=VASP_A
        )
        assert match is not None
        assert match.entity.category == EntityType.VASP
        assert match.entity.name == "Candidate VASP alpha"
        assert match.entity.tag_source == "fixture_list_v1"
        assert match.match_type == "exact"

    async def test_register_is_idempotent(self, session) -> None:
        for _ in range(2):
            await REGISTRY.register(
                session,
                chain_id="ethereum",
                network="mainnet",
                address=VASP_A,
                category=EntityType.VASP,
            )
        count = (await session.execute(select(func.count()).select_from(EntityAddressRecord))).scalar_one()
        entities = (await session.execute(select(func.count()).select_from(EntityRecord))).scalar_one()
        assert count == 1
        assert entities == 1

    async def test_register_normalizes_case(self, session) -> None:
        await REGISTRY.register(
            session,
            chain_id="ethereum",
            network="mainnet",
            address=VASP_A.upper(),
            category=EntityType.BRIDGE,
        )
        match = await REGISTRY.lookup(
            session, chain_id="ethereum", network="mainnet", address=VASP_A
        )
        assert match is not None
        assert match.entity.category == EntityType.BRIDGE
        assert match.address == VASP_A


class TestLookup:
    async def test_network_specific_row_preferred_over_chainwide(self, session) -> None:
        await REGISTRY.register(
            session, chain_id="ethereum", network=None, address=VASP_A, category=EntityType.OTHER
        )
        await REGISTRY.register(
            session,
            chain_id="ethereum",
            network="mainnet",
            address=VASP_A,
            category=EntityType.VASP,
        )
        match = await REGISTRY.lookup(
            session, chain_id="ethereum", network="mainnet", address=VASP_A
        )
        assert match.entity.category == EntityType.VASP

    async def test_falls_back_to_chainwide_row(self, session) -> None:
        await REGISTRY.register(
            session, chain_id="ethereum", network=None, address=VASP_A, category=EntityType.MIXER
        )
        match = await REGISTRY.lookup(
            session, chain_id="ethereum", network="sepolia", address=VASP_A
        )
        assert match is not None
        assert match.entity.category == EntityType.MIXER

    async def test_chain_is_respected(self, session) -> None:
        await REGISTRY.register(
            session, chain_id="ethereum", network="mainnet", address=VASP_A, category=EntityType.VASP
        )
        assert (
            await REGISTRY.lookup(session, chain_id="tron", network="mainnet", address=VASP_A)
            is None
        )

    async def test_unknown_address_returns_none(self, session) -> None:
        assert (
            await REGISTRY.lookup(session, chain_id="ethereum", network="mainnet", address=eth_addr(999))
            is None
        )

    async def test_lookup_many_returns_subset(self, session) -> None:
        await REGISTRY.register(
            session, chain_id="ethereum", network="mainnet", address=VASP_A, category=EntityType.VASP
        )
        await REGISTRY.register(
            session, chain_id="ethereum", network="mainnet", address=MIXER, category=EntityType.MIXER
        )
        matches = await REGISTRY.lookup_many(
            session,
            chain_id="ethereum",
            network="mainnet",
            addresses=[VASP_A, VASP_B, MIXER],
        )
        assert set(matches) == {VASP_A, MIXER}
        assert matches[VASP_A].entity.category == EntityType.VASP
        assert matches[MIXER].entity.category == EntityType.MIXER

    async def test_lookup_many_empty(self, session) -> None:
        assert await REGISTRY.lookup_many(session, chain_id="ethereum", network="mainnet", addresses=[]) == {}