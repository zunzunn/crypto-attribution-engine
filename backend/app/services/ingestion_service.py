"""High-level ingestion orchestration shared by the API and scripts.

Flow: validate address -> create audit run -> chain adapter fetch+normalize ->
idempotent upsert -> close the run. Idempotency holds because transactions
are keyed by (chain_id, network, tx_hash): re-ingesting an address inserts
nothing new and simply records a new audit run.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AttributionEngineError
from app.repositories import IngestionRunRepository, TransactionRepository
from app.repositories.transaction_repo import orm_to_canonical
from app.schemas import IngestionRunSummary, Transaction
from app.services.ingestion.registry import IngestionRegistry
from app.utils.addresses import validate_chain_address

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        registry: IngestionRegistry,
        transactions: TransactionRepository,
        runs: IngestionRunRepository,
    ) -> None:
        self._registry = registry
        self._transactions = transactions
        self._runs = runs

    async def ingest_address(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        address: str,
        network: str | None = None,
    ) -> IngestionRunSummary:
        address = validate_chain_address(chain_id, address)

        adapter = self._registry.get(chain_id)
        resolved_network = network or adapter.default_network

        run = await self._runs.create(
            session, chain_id=chain_id, network=resolved_network, address=address
        )
        run_id = run.id
        try:
            transactions: list[Transaction] = await adapter.get_normalized_transactions(address)
            inserted, skipped = await self._transactions.upsert_many(session, transactions)
            await self._runs.complete(
                session,
                run=run,
                status="success",
                total_fetched=len(transactions),
                inserted=inserted,
                skipped_existing=skipped,
            )
            await session.commit()
            logger.info(
                "ingest chain=%s address=%s run=%s fetched=%d inserted=%d skipped=%d",
                chain_id, address, run_id, len(transactions), inserted, skipped,
            )
            await session.refresh(run)
            return self._summary(run)
        except AttributionEngineError:
            await session.rollback()
            await self._runs.complete(
                session, run=run, status="failed",
                total_fetched=0, inserted=0, skipped_existing=0,
            )
            await session.commit()
            raise
        except Exception as exc:  # pragma: no cover - defensive
            await session.rollback()
            logger.exception("ingestion failed for %s/%s", chain_id, address)
            raise AttributionEngineError(f"Ingestion failed for {chain_id}/{address}") from exc

    async def get_run(self, session: AsyncSession, run_id: int) -> IngestionRunSummary | None:
        run = await self._runs.get(session, run_id)
        return self._summary(run) if run else None

    async def list_transactions_for_address(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        address: str,
        network: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        address = validate_chain_address(chain_id, address)
        rows = await self._transactions.list_by_address(
            session,
            address=address,
            chain_id=chain_id,
            network=network,
            limit=limit,
            offset=offset,
        )
        return [orm_to_canonical(row) for row in rows]

    async def get_transaction_by_hash(
        self,
        session: AsyncSession,
        *,
        chain_id: str,
        network: str | None,
        tx_hash: str,
    ) -> Transaction | None:
        row = await self._transactions.get_by_hash(
            session, chain_id=chain_id, network=network, tx_hash=tx_hash.lower()
        )
        return orm_to_canonical(row) if row else None

    @staticmethod
    def _summary(run) -> IngestionRunSummary:
        return IngestionRunSummary(
            ingestion_run_id=run.id,
            chain_id=run.chain_id,
            network=run.network,
            address=run.address,
            status=run.status,
            total_fetched=run.total_fetched,
            inserted=run.inserted,
            skipped_existing=run.skipped_existing,
            started_at=run.started_at,
            finished_at=run.finished_at,
            error_message=run.error_message,
        )