"""FastAPI application factory.

``create_app`` owns the engine/session factory and the adapter registry so
tests can inject an in-memory SQLite engine and a stubbed adapter registry
while production uses the PostgreSQL engine from ``backend/.env``.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import attribution_router, health_router, ingest_router
from app.core.config import Settings, get_settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.engine import build_session_factory
from app.repositories import IngestionRunRepository, TransactionRepository
from app.services.attribution.registry import DatabaseAddressRegistry
from app.services.attribution.scoring import ConfidenceScorer
from app.services.attribution.service import AttributionService
from app.services.graph.repository import DatabaseGraphExpander
from app.services.ingestion.registry import IngestionRegistry
from app.services.ingestion_service import IngestionService
from app.services.traversal.engine import TraversalEngine

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None,
    *,
    session_factory=None,
    registry: IngestionRegistry | None = None,
) -> FastAPI:
    cfg = settings or get_settings()
    setup_logging(cfg.log_level)

    sf = session_factory if session_factory is not None else build_session_factory(cfg.database_url)
    registry = registry or IngestionRegistry(cfg)

    ingestion_service = IngestionService(
        registry=registry,
        transactions=TransactionRepository(),
        runs=IngestionRunRepository(),
    )

    attribution_service = AttributionService(
        engine=TraversalEngine(),
        expander=DatabaseGraphExpander(),
        registry=DatabaseAddressRegistry(),
        scorer=ConfidenceScorer(),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if cfg.db_auto_create:
            try:
                from app import models  # noqa: F401  (register all models on metadata)

                async with sf.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
            except Exception as exc:  # noqa: BLE001 - startup must not crash the API
                logger.warning("db_auto_create failed (is PostgreSQL running?): %s", exc)
        try:
            yield
        finally:
            await sf.dispose()

    app = FastAPI(
        title=cfg.app_name,
        version=cfg.app_version,
        description="Blockchain transaction ingestion for the Crypto Attribution Engine.",
        lifespan=lifespan,
    )

    app.state.settings = cfg
    app.state.session_factory = sf
    app.state.registry = registry
    app.state.ingestion_service = ingestion_service
    app.state.attribution_service = attribution_service

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(ingest_router, prefix=cfg.api_prefix)
    app.include_router(attribution_router, prefix=cfg.api_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {"service": cfg.app_name, "version": cfg.app_version, "docs": "/docs"}

    return app