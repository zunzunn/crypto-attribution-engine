"""API package."""

from app.api.routes.attribution import router as attribution_router
from app.api.routes.health import router as health_router
from app.api.routes.ingest import router as ingest_router

__all__ = ["attribution_router", "health_router", "ingest_router"]