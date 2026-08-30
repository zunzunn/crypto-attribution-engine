"""Transaction persistence with idempotent upserts.

Strategy: select the hashes that already exist for the batch's
(chain_id, network) window, insert only the missing rows. This is
dialect-agnostic (works on PostgreSQL and SQLite) and returns inserted vs.
skipped counts for the ingestion audit trail. The unique constraint on
(chain_id, network, tx_hash) is the backstop that guarantees idempotency even
under concurrent writes.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TransactionRecord
from app.schemas import Transaction
from app.utils.time import as_aware_utc, as_naive_utc


def canonical_to_orm(tx: Transaction) -> TransactionRecord:
    """Convert the canonical schema to an ORM row (UTC-naive storage).

    The provider's raw payload is not part of the canonical schema; raw
    persistence is a documented candidate for the ingestion benefits pass.
    """
    return TransactionRecord(
        chain_id=tx.chain_id,
        network=tx.network,
        tx_hash=tx.tx_hash,
        block_number=tx.block_number,
        block_hash=tx.block_hash,
        block_timestamp=as_naive_utc(tx.block_timestamp),
        status=tx.status,
        transaction_type=tx.transaction_type,
        from_address=tx.from_address,
        to_address=tx.to_address,
        value=tx.value,
        value_decimals=tx.value_decimals,
        fee=tx.fee,
        input_data=tx.input_data,
        senders=[m.model_dump() for m in tx.senders] if tx.senders else None,
        recipients=[m.model_dump() for m in tx.recipients] if tx.recipients else None,
        source=tx.source,
        fetched_at=as_naive_utc(tx.fetched_at),
        raw=None,
    )


def orm_to_canonical(row: TransactionRecord) -> Transaction:
    """Convert an ORM row back into the canonical schema (aware UTC)."""
    return Transaction(
        chain_id=row.chain_id,
        network=row.network,
        tx_hash=row.tx_hash,
        block_number=row.block_number,
        block_hash=row.block_hash,
        block_timestamp=as_aware_utc(row.block_timestamp),
        status=row.status,
        transaction_type=row.transaction_type,
        from_address=row.from_address,
        to_address=row.to_address,
        value=row.value,
        value_decimals=row.value_decimals,
        fee=row.fee,
        input_data=row.input_data,
        senders=row.senders or [],
        recipients=row.recipients or [],
        source=row.source,
        fetched_at=as_aware_utc(row.fetched_at),
        raw=None,
    )


def _dedupe_records(records: Iterable[TransactionRecord]) -> list[TransactionRecord]:
    """Collapse duplicate rows in a single batch by (chain_id, network, tx_hash).

    Keeps the first occurrence so re-ingested batches are idempotent even before
    the unique constraint is consulted.
    """
    seen: set[tuple[str, str, str]] = set()
    unique: list[TransactionRecord] = []
    for record in records:
        key = (record.chain_id, record.network, record.tx_hash)
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


class TransactionRepository:
    async def upsert_many(
        self, session: AsyncSession, transactions: Iterable[Transaction]
    ) -> tuple[int, int]:
        """Insert new canonical transactions; return (inserted, skipped_existing)."""
        records = _dedupe_records(canonical_to_orm(tx) for tx in transactions)
        if not records:
            return 0, 0

        chain_id = records[0].chain_id
        network = records[0].network
        hashes = {r.tx_hash for r in records}

        existing = await session.execute(
            select(TransactionRecord.tx_hash).where(
                TransactionRecord.chain_id == chain_id,
                TransactionRecord.network == network,
                TransactionRecord.tx_hash.in_(hashes),
            )
        )
        existing_hashes = {row for (row,) in existing.all()}

        new_records = [r for r in records if r.tx_hash not in existing_hashes]
        session.add_all(new_records)
        await session.flush()
        return len(new_records), len(records) - len(new_records)

    async def list_by_address(
        self,
        session: AsyncSession,
        *,
        address: str,
        chain_id: str,
        network: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TransactionRecord]:
        stmt = (
            select(TransactionRecord)
            .where(
                TransactionRecord.chain_id == chain_id,
                (TransactionRecord.from_address == address)
                | (TransactionRecord.to_address == address),
            )
            .order_by(TransactionRecord.block_number.desc(), TransactionRecord.tx_hash.asc())
            .limit(limit)
            .offset(offset)
        )
        if network:
            stmt = stmt.where(TransactionRecord.network == network)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_hash(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        network: str | None,
        tx_hash: str,
    ) -> TransactionRecord | None:
        stmt = select(TransactionRecord).where(
            TransactionRecord.chain_id == chain_id,
            TransactionRecord.tx_hash == tx_hash,
        )
        if network:
            stmt = stmt.where(TransactionRecord.network == network)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_address(
        self,
        session: AsyncSession,
        *,
        address: str,
        chain_id: str,
        network: str | None = None,
    ) -> int:
        stmt = (
            select(TransactionRecord)
            .where(
                TransactionRecord.chain_id == chain_id,
                (TransactionRecord.from_address == address)
                | (TransactionRecord.to_address == address),
            )
        )
        if network:
            stmt = stmt.where(TransactionRecord.network == network)
        stmt = stmt.with_only_columns(func.count())
        result = await session.execute(stmt)
        return int(result.scalar_one())