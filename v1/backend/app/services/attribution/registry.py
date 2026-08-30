"""Entity/address registry abstraction + a local, database-backed implementation.

The registry associates wallet addresses with known entities (VASP, MIXER,
BRIDGE, DEX, SCAM, RANSOMWARE, OTHER). The initial implementation is local and
explicitly NOT comprehensive: it seeds from whatever the operator registers. It
is designed so an external intelligence source can be added later by
implementing the same ``AddressRegistry`` protocol without touching traversal
or attribution logic.

Only *exact* known address matches are produced here (a verbatim address==known
address). Cluster/contract matching layers are documented follow-ons.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import EntityAddressRecord, EntityRecord
from app.schemas import Entity, EntityMatch, EntityType
from app.utils.time import as_aware_utc, utc_now


class AddressRegistry(Protocol):
    """Anything that can answer 'does this address belong to a known entity?'."""

    async def lookup(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        network: str | None,
        address: str,
    ) -> EntityMatch | None:
        ...

    async def lookup_many(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        network: str | None,
        addresses: list[str],
    ) -> dict[str, EntityMatch]:
        ...


def _to_category(category: str) -> EntityType:
    try:
        return EntityType(category)
    except ValueError:
        return EntityType.OTHER


def _orm_to_match(record: EntityAddressRecord) -> EntityMatch:
    return EntityMatch(
        address=record.address,
        chain_id=record.chain_id,
        network=record.network,
        entity=Entity(
            category=_to_category(record.entity.category),
            name=record.entity.name,
            tag_source=record.entity.tag_source,
            tag_version=record.entity.tag_version,
        ),
        match_type="exact",
        imported_at=as_aware_utc(record.imported_at),
    )


class DatabaseAddressRegistry:
    """Local PostgreSQL-backed registry over ``entities`` + ``entity_addresses``."""

    async def register(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        address: str,
        category: EntityType | str,
        name: str | None = None,
        network: str | None = None,
        tag_source: str = "local",
        tag_version: str = "v1",
        imported_at: datetime | None = None,
        note: str | None = None,
    ) -> EntityMatch:
        """Register one known address->entity mapping (idempotent).

        Re-registering the same (chain_id, network, address) updates nothing
        and returns the existing match - the mapping table has a unique key.
        """
        address = address.strip().lower()
        category_value = category.value if isinstance(category, EntityType) else str(category)

        stmt = (
            select(EntityAddressRecord)
            .options(selectinload(EntityAddressRecord.entity))
            .where(
                EntityAddressRecord.chain_id == chain_id,
                EntityAddressRecord.network == (network if network else None),
                EntityAddressRecord.address == address,
            )
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return _orm_to_match(existing)

        entity = EntityRecord(
            category=category_value,
            name=name,
            tag_source=tag_source,
            tag_version=tag_version,
        )
        session.add(entity)
        await session.flush()

        record = EntityAddressRecord(
            entity_id=entity.id,
            chain_id=chain_id,
            network=network,
            address=address,
            imported_at=(imported_at or utc_now()).replace(tzinfo=None),
            note=note,
        )
        session.add(record)
        await session.flush()
        await session.refresh(record, attribute_names=["entity"])
        return _orm_to_match(record)

    async def lookup(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        network: str | None,
        address: str,
    ) -> EntityMatch | None:
        return (await self.lookup_many(session, chain_id=chain_id, network=network,
                                       addresses=[address])).get(address)

    async def lookup_many(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        network: str | None,
        addresses: list[str],
    ) -> dict[str, EntityMatch]:
        if not addresses:
            return {}

        stmt = (
            select(EntityAddressRecord)
            .options(selectinload(EntityAddressRecord.entity))
            .join(EntityAddressRecord.entity)
            .where(
                EntityAddressRecord.chain_id == chain_id,
                EntityAddressRecord.address.in_(addresses),
            )
            .order_by(EntityAddressRecord.network.desc().nullslast(), EntityAddressRecord.address)
        )
        if network:
            # Prefer an exact network row; fall back to chain-wide (network IS NULL).
            stmt = stmt.where(
                (EntityAddressRecord.network == network)
                | (EntityAddressRecord.network.is_(None))
            )

        matches: dict[str, EntityMatch] = {}
        for record in (await session.execute(stmt)).scalars():
            if record.address not in matches:
                matches[record.address] = _orm_to_match(record)
        return matches