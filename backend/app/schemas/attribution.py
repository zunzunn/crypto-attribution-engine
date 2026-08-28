"""Attribution schemas: entities, matches, confidence, candidates, responses.

Terminology follows the constraints in REQUIREMENTS.md / ATTRIBUTION.md: the
engine produces *known address matches*, *candidate VASPs*, and *attribution
confidence* -- never a claim of definitive wallet ownership. Confidence here is
attribution confidence only; criminal/risk scoring belongs to Phase 3.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.traversal import EvidencePath, TraversalRequest, TraversalResult


class EntityType(str, Enum):
    """Entity categories the registry can associate addresses with."""

    VASP = "VASP"
    MIXER = "MIXER"
    BRIDGE = "BRIDGE"
    DEX = "DEX"
    SCAM = "SCAM"
    RANSOMWARE = "RANSOMWARE"
    OTHER = "OTHER"


class Entity(BaseModel):
    """A known entity (service or actor category) that addresses map to."""

    category: EntityType
    name: str | None = Field(default=None, description="Human label, e.g. 'Candidate VASP alpha'")
    tag_source: str = Field(description="Originating tag dataset, e.g. 'curated_vasp_list_v3'")
    tag_version: str = Field(description="Version of the tag dataset")


class EntityMatch(BaseModel):
    """A known address match: a wallet address linked to an entity.

    ``match_type`` is exactly "exact" in this version (a verbatim address match
    against the local registry); cluster/contract matching layers are deferred.
    """

    address: str
    chain_id: str
    network: str | None = None
    entity: Entity
    match_type: Literal["exact"] = "exact"
    imported_at: datetime | None = Field(
        default=None, description="When this mapping entered the registry (tag freshness)"
    )


class ConfidenceFactor(BaseModel):
    """One named, signed adjustment to the attribution confidence score."""

    name: str
    delta: float
    reason: str


class ConfidenceResult(BaseModel):
    """Explainable attribution confidence in [0, 1] plus its factor breakdown."""

    base_score: float
    score: float
    tier: Literal["high", "medium", "low", "very_low"]
    scoring_model_version: str
    factors: list[ConfidenceFactor] = Field(default_factory=list)


class AttributionCandidate(BaseModel):
    """A ranked candidate: a discovered address that matched a known entity."""

    entity: Entity
    matched_address: str
    chain_id: str
    network: str | None = None
    hop_count: int
    path: EvidencePath
    evidence_tx_hashes: list[str] = Field(default_factory=list)
    match_type: Literal["exact"] = "exact"
    tag_source: str
    tag_version: str
    confidence: ConfidenceResult


class AttributionInvestigationResponse(BaseModel):
    """Full result of one investigate() call: traversal + ranked candidates."""

    request: TraversalRequest
    traversal: TraversalResult
    candidates: list[AttributionCandidate] = Field(default_factory=list)
    scoring_model_version: str
    message: str | None = Field(
        default=None, description="Human note (e.g. no known-address matches found)"
    )