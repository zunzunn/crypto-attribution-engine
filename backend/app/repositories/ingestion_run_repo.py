"""Ingestion run metadata persistence."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IngestionRunRecord
from app.utils.time import utc_now


class IngestionRunRepository:
    async def create(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        network: str | None,
        address: str,
    ) -> IngestionRunRecord:
        run = IngestionRunRecord(
            chain_id=chain_id,
            network=network,
            address=address,
            status="running",
            started_at=utc_now().replace(tzinfo=None),
        )
        session.add(run)
        await session.flush()
        return run

    async def complete(
        self,
        session: AsyncSession,
        *,
        run: IngestionRunRecord,
        status: str,
        total_fetched: int,
        inserted: int,
        skipped_existing: int,
        error_message: str | None = None,
    ) -> None:
        run.status = status
        run.total_fetched = total_fetched
        run.inserted = inserted
        run.skipped_existing = skipped_existing
        run.error_message = error_message
        run.finished_at = utc_now().replace(tzinfo=None)
        await session.flush()

    async def get(self, session: AsyncSession, run_id: int) -> IngestionRunRecord | None:
        return await session.get(IngestionRunRecord, run_id)