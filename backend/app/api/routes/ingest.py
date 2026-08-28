"""Ingestion + transaction query endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    AttributionEngineError,
    ChainNotSupportedError,
    InvalidAddressError,
    ProviderError,
    RateLimitError,
)
from app.db.session import get_session
from app.schemas import IngestionRunSummary, Transaction
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ingestion"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _ingestion_service(request: Request) -> IngestionService:
    return request.app.state.ingestion_service


@router.post(
    "/ingest/{chain_id}/{address}",
    response_model=IngestionRunSummary,
    summary="Ingest transaction history for an address",
    description=(
        "Fetches native transactions for an address from the chain's data provider, "
        "normalizes them into the canonical model, and persists them idempotently "
        "(re-ingesting the same transaction never duplicates a row)."
    ),
)
async def ingest_address(
    chain_id: str = Path(..., description="Chain id, e.g. 'ethereum'"),
    address: str = Path(..., description="Wallet address to trace"),
    session: SessionDep = None,
    request: Request = None,
) -> IngestionRunSummary:
    service = _ingestion_service(request)
    try:
        return await service.ingest_address(session, chain_id=chain_id, address=address)
    except ChainNotSupportedError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidAddressError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except AttributionEngineError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/ingest/{chain_id}/{address}", response_model=list[Transaction])
async def list_transactions(
    chain_id: str = Path(...),
    address: str = Path(...),
    session: SessionDep = None,
    request: Request = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[Transaction]:
    service = _ingestion_service(request)
    try:
        return await service.list_transactions_for_address(
            session, chain_id=chain_id, address=address, limit=limit, offset=offset
        )
    except ChainNotSupportedError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidAddressError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/ingestion-runs/{run_id}", response_model=IngestionRunSummary)
async def get_ingestion_run(
    run_id: int = Path(...),
    session: SessionDep = None,
    request: Request = None,
) -> IngestionRunSummary:
    service = _ingestion_service(request)
    run = await service.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ingestion run not found")
    return run


@router.get("/transactions/{tx_hash}", response_model=Transaction)
async def get_transaction(
    tx_hash: str = Path(...),
    chain_id: str = Query(default="ethereum"),
    network: str | None = Query(default=None),
    session: SessionDep = None,
    request: Request = None,
) -> Transaction:
    service = _ingestion_service(request)
    tx = await service.get_transaction_by_hash(
        session, chain_id=chain_id, network=network, tx_hash=tx_hash
    )
    if tx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="transaction not found")
    return tx