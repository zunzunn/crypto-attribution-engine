"""Attribution orchestration: traverse the derived graph, match discovered
addresses against the entity registry, score confidence, and rank candidates.

Language discipline: we emit *known address matches* and *candidate VASPs*
with *attribution confidence* - never a claim that an address owner has been
definitively identified. Confidence here is attribution confidence only.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AttributionEngineError
from app.schemas import (
    AttributionCandidate,
    AttributionInvestigationResponse,
    TraversalRequest,
)
from app.schemas.graph import GraphEdge
from app.services.attribution.registry import AddressRegistry
from app.services.attribution.scoring import SCORING_MODEL_VERSION, ConfidenceScorer
from app.services.graph.repository import GraphExpander
from app.services.traversal.engine import TraversalEngine
from app.utils.addresses import validate_chain_address

logger = logging.getLogger(__name__)


class AttributionService:
    def __init__(
        self,
        *,
        engine: TraversalEngine,
        expander: GraphExpander,
        registry: AddressRegistry,
        scorer: ConfidenceScorer,
    ) -> None:
        self._engine = engine
        self._expander = expander
        self._registry = registry
        self._scorer = scorer

    async def investigate(
        self,
        session: AsyncSession,
        request: TraversalRequest,
    ) -> AttributionInvestigationResponse:
        seed = validate_chain_address(request.chain_id, request.seed_address)
        normalized = request.model_copy(update={"seed_address": seed})

        def expand(address: str) -> Awaitable[list[GraphEdge]]:
            return self._expander.outgoing(
                session,
                chain_id=request.chain_id,
                network=request.network,
                address=address,
            )

        try:
            traversal = await self._engine.traverse(request=normalized, expand=expand)
        except Exception as exc:
            logger.exception("attribution traversal failed for %s/%s", request.chain_id, seed)
            raise AttributionEngineError(
                f"Investigation failed for {request.chain_id}/{seed}"
            ) from exc

        discovered = traversal.discovered_addresses
        matches = await self._registry.lookup_many(
            session,
            chain_id=request.chain_id,
            network=request.network,
            addresses=discovered,
        )

        candidates: list[AttributionCandidate] = []
        for path in traversal.paths:
            match = matches.get(path.target_address)
            if match is None:
                continue

            support_edges = traversal.node_incoming_edges.get(path.target_address, [])
            evidence_hashes = sorted({e.tx_hash for e in support_edges if e.tx_hash})

            confidence = self._scorer.score(
                hop_count=path.hop_count,
                evidence_tx_hashes=evidence_hashes,
                imported_at=match.imported_at,
                path_edges=[hop.edge for hop in path.hops],
            )

            candidates.append(
                AttributionCandidate(
                    entity=match.entity,
                    matched_address=path.target_address,
                    chain_id=request.chain_id,
                    network=match.network,
                    hop_count=path.hop_count,
                    path=path,
                    evidence_tx_hashes=evidence_hashes,
                    match_type=match.match_type,
                    tag_source=match.entity.tag_source,
                    tag_version=match.entity.tag_version,
                    confidence=confidence,
                )
            )

        candidates.sort(
            key=lambda c: (
                -c.confidence.score,
                c.hop_count,
                c.matched_address,
            )
        )

        return AttributionInvestigationResponse(
            request=normalized,
            traversal=traversal,
            candidates=candidates,
            scoring_model_version=SCORING_MODEL_VERSION,
            message=(
                None
                if candidates
                else "No known-address matches found within the explored graph."
            ),
        )