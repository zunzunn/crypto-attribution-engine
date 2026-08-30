"""Development-only demo seeding CLI.

Seeds a deterministic, synthetic SEED -> INTER -> VASP_A graph plus a
versioned, clearly-marked demo entity ("Candidate VASP alpha") into the
development database so endpoints such as
``POST /api/v1/attribution/investigate`` can be exercised manually.

ATTENTION: this is FAKE data for local/QA testing only. The addresses are
dummy values (``0x0000…0001`` style), never real exchange/VASP wallets, and
the entity tag source (``demo_fixture_v1``) marks it unambiguously as a
development fixture. Never point this at a production database.

Usage (from ``v1/backend/``):

    .venv/bin/python -m app.dev.seed_demo            # seed (idempotent)
    .venv/bin/python -m app.dev.seed_demo --reset    # remove demo data only

Wrappers: ``make seed-demo`` / ``make reset-demo`` (repo root).
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass

from sqlalchemy import delete

import app.models  # noqa: F401  (register all models on metadata, for create_all)
from app.core.config import Settings
from app.db.base import Base
from app.db.engine import AsyncSessionFactory, build_session_factory
from app.dev import demo_data
from app.models import EntityAddressRecord, EntityRecord, TransactionRecord
from app.repositories.transaction_repo import TransactionRepository
from app.services.attribution.registry import DatabaseAddressRegistry

SYNTHETIC_BANNER = (
    "\n"
    "  ==========================================================================\n"
    "  SYNTHETIC DEMO DATA - FOR LOCAL/QA TESTING ONLY. NOT REAL ENTITIES.\n"
    "  Addresses are dummy values; the entity tag source is\n"
    f"  '{demo_data.VASP_A_TAG_SOURCE}'. Do not use with production data.\n"
    "  ==========================================================================\n"
)


@dataclass
class SeedResult:
    inserted: int
    skipped: int
    entity_address: str
    entity_name: str
    entity_tag_source: str

    def format(self) -> str:
        return (
            f"Demo graph seeded: {demo_data.SEED} -> {demo_data.INTER} -> {demo_data.VASP_A}\n"
            f"  transactions inserted: {self.inserted}, already present (skipped): {self.skipped}\n"
            f"  entity: {self.entity_name!r} ({self.entity_address}) "
            f"tag_source={self.entity_tag_source}\n"
            f"  Try: POST /api/v1/attribution/investigate\n"
            f"       {{'chain_id': '{demo_data.DEMO_CHAIN}', 'network': "
            f"'{demo_data.DEMO_NETWORK}', 'seed_address': '{demo_data.SEED}'}}\n"
        )


@dataclass
class ResetResult:
    transactions_deleted: int
    address_links_deleted: int
    entities_deleted: int

    def format(self) -> str:
        return (
            "Demo data removed:\n"
            f"  transactions deleted: {self.transactions_deleted}\n"
            f"  entity-address links deleted: {self.address_links_deleted}\n"
            f"  entity records deleted (tag_source={demo_data.VASP_A_TAG_SOURCE}): "
            f"{self.entities_deleted}\n"
        )


async def ensure_schema(factory: AsyncSessionFactory) -> None:
    """Create missing tables (dev convenience; additive only)."""
    async with factory.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_demo(factory: AsyncSessionFactory) -> SeedResult:
    """Seed the synthetic demo graph + entity. Idempotent."""
    transactions = demo_data.build_transactions()
    repo = TransactionRepository()
    registry = DatabaseAddressRegistry()

    async with factory() as session:
        inserted, skipped = await repo.upsert_many(session, transactions)
        match = await registry.register(
            session,
            chain_id=demo_data.DEMO_CHAIN,
            network=demo_data.DEMO_NETWORK,
            address=demo_data.VASP_A,
            category=demo_data.VASP_A_ENTITY_CATEGORY,
            name=demo_data.VASP_A_NAME,
            tag_source=demo_data.VASP_A_TAG_SOURCE,
            tag_version=demo_data.VASP_A_TAG_VERSION,
            imported_at=demo_data.DEMO_BASE,
            note="SYNTHETIC demo fixture for manual API testing - not a real entity.",
        )
        await session.commit()

    return SeedResult(
        inserted=inserted,
        skipped=skipped,
        entity_address=match.address,
        entity_name=match.entity.name or demo_data.VASP_A_NAME,
        entity_tag_source=match.entity.tag_source,
    )


async def reset_demo(factory: AsyncSessionFactory) -> ResetResult:
    """Remove only demo-owned rows (demo tx hashes / demo tag source)."""
    async with factory() as session:
        tx_result = await session.execute(
            delete(TransactionRecord).where(
                TransactionRecord.chain_id == demo_data.DEMO_CHAIN,
                TransactionRecord.network == demo_data.DEMO_NETWORK,
                TransactionRecord.tx_hash.in_(demo_data.demo_tx_hashes()),
            )
        )

        links_result = await session.execute(
            delete(EntityAddressRecord).where(
                EntityAddressRecord.chain_id == demo_data.DEMO_CHAIN,
                EntityAddressRecord.network == demo_data.DEMO_NETWORK,
                EntityAddressRecord.address == demo_data.VASP_A,
            )
        )

        ent_result = await session.execute(
            delete(EntityRecord).where(EntityRecord.tag_source == demo_data.VASP_A_TAG_SOURCE)
        )
        await session.commit()

    return ResetResult(
        transactions_deleted=tx_result.rowcount or 0,
        address_links_deleted=links_result.rowcount or 0,
        entities_deleted=ent_result.rowcount or 0,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed or reset SYNTHETIC demo data in the development database.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove demo-owned rows instead of seeding.",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="SQLAlchemy async URL. Defaults to DATABASE_URL from backend/.env.",
    )
    parser.add_argument(
        "--echo",
        action="store_true",
        help="Echo SQL (SQLAlchemy) while running.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    settings = Settings()
    database_url = args.database_url or settings.database_url
    factory = build_session_factory(database_url, echo=args.echo)

    async def _run() -> None:
        try:
            await ensure_schema(factory)
            if args.reset:
                result = await reset_demo(factory)
            else:
                result = await seed_demo(factory)
        finally:
            await factory.dispose()

        print(SYNTHETIC_BANNER)
        print(result.format())

    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())