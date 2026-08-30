"""Ingestion run schemas (metadata returned by the API)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class IngestionRunCreate(BaseModel):
    chain_id: str
    network: str | None = None
    address: str


class IngestionRunSummary(BaseModel):
    ingestion_run_id: int
    chain_id: str
    network: str | None = None
    address: str
    status: str
    total_fetched: int = Field(default=0, description="transactions fetched from provider")
    inserted: int = Field(default=0, description="new rows written")
    skipped_existing: int = Field(default=0, description="rows already present (idempotency)")
    started_at: datetime
    finished_at: datetime | None = None
    error_message: str | None = None