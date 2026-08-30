"""Attribution investigation endpoints (Phase 2)."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    AttributionEngineError,
    ChainNotSupportedError,
    InvalidAddressError,
)
from app.db.session import get_session
from app.schemas import AttributionInvestigationResponse, TraversalRequest
from app.services.attribution.service import AttributionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/attribution", tags=["attribution"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _attribution_service(request: Request) -> AttributionService:
    return request.app.state.attribution_service


@router.post(
    "/investigate",
    response_model=AttributionInvestigationResponse,
    summary="Run a bounded traversal and return ranked attribution candidates",
    description=(
        "Derives a directed transaction graph from persisted transactions, runs a "
        "bounded forward BFS from the suspect wallet, matches discovered addresses "
        "against the local known-entity registry, and returns every evidence path "
        "plus ranked candidate attributions with explainable confidence. Produces "
        "candidate attributions only - it never claims definitive wallet ownership."
    ),
)
async def investigate(
    request_body: TraversalRequest,
    session: SessionDep = None,
    request: Request = None,
) -> AttributionInvestigationResponse:
    service = _attribution_service(request)
    try:
        return await service.investigate(session, request_body)
    except ChainNotSupportedError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidAddressError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except AttributionEngineError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc