"""GET /health — liveness + database readiness."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.schemas import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, responses={503: {"model": HealthResponse}})
async def health(request: Request) -> HealthResponse | JSONResponse:
    settings = get_settings()
    database_status = "ok"
    status_code = 200
    try:
        factory = request.app.state.session_factory
        async with factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - health must never raise
        logger.warning("health check database ping failed: %s", exc)
        database_status = f"unavailable: {type(exc).__name__}"
        status_code = 503

    payload = HealthResponse(
        status="ok" if status_code == 200 else "degraded",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        database=database_status,
    )
    if status_code != 200:
        return JSONResponse(status_code=status_code, content=payload.model_dump())
    return payload