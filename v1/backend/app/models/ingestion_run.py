"""ORM model for ingestion run audit records.

Re-ingesting an address creates a new run row (auditable), while transaction
rows stay deduplicated thanks to the unique constraint on ``transactions``.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IngestionRunRecord(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chain_id: Mapped[str] = mapped_column(String(32), nullable=False)
    network: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    total_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_existing: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<IngestionRunRecord id={self.id} chain={self.chain_id} addr={self.address[:10]}...>"