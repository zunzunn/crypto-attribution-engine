"""Risk scoring schemas: indicators, assessments, levels, and configuration."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Qualitative risk tier for a risk assessment."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskIndicator(BaseModel):
    """A single detected high-risk behavioral indicator."""

    indicator_type: str
    points: int
    explanation: str
    supporting_addresses: list[str] = Field(
        default_factory=list,
        description="Addresses involved in this indicator.",
    )
    supporting_tx_hashes: list[str] = Field(
        default_factory=list,
        description="Transaction hashes supporting this indicator.",
    )
    evidence: dict = Field(
        default_factory=dict,
        description="Relevant evidence from the traversal/graph.",
    )


class RiskAssessment(BaseModel):
    """Complete risk assessment for a traversal investigation."""

    risk_level: RiskLevel
    total_score: int = Field(
 ge=0, le=100, description="Total risk score in [0, 100]."
    )
    indicators: list[RiskIndicator] = Field(
        default_factory=list,
        description="Detected risk indicators with points and evidence.",
    )
    category_breakdown: dict[str, int] = Field(
        default_factory=dict,
        description="Points per category (entity_risk, behavioral, graph_structure).",
    )
    model_config = {"frozen": True}


class RiskScoringConfig(BaseModel):
    """Configurable weights and caps for risk scoring."""

    # Entity risk indicators (sanctions, ransomware, fraud, darknet)
    entity_risk_weight_sanctions: int = Field(
        default=40, ge=0, description="Points for sanctions/high-risk entity interaction."
    )
    entity_risk_weight_ransomware: int = Field(
        default=35, ge=0, description="Points for ransomware-linked entity interaction."
    )
    entity_risk_weight_fraud: int = Field(
        default=30, ge=0, description="Points for fraud-linked entity interaction."
    )
    entity_risk_weight_darknet: int = Field(
        default=30, ge=0, description="Points for darknet-linked entity interaction (deferred)."
    )
    entity_risk_cap: int = Field(
        default=40, ge=0, description="Category cap for entity risk indicators."
    )

    # Behavioral indicators (mixer, rapid multi-hop, cross-chain)
    behavioral_weight_mixer: int = Field(
        default=25, ge=0, description="Points for mixer interaction."
    )
    behavioral_weight_rapid_hop: int = Field(
        default=10, ge=0, description="Points for rapid multi-hop movement."
    )
    behavioral_weight_cross_chain: int = Field(
        default=10, ge=0, description="Points for cross-chain movement (deferred)."
    )
    behavioral_cap: int = Field(
        default=35, ge=0, description="Category cap for behavioral indicators."
    )

    # Graph structure indicators (complexity, fragmentation)
    graph_weight_complexity: int = Field(
        default=10, ge=0, description="Points for high graph complexity."
    )
    graph_weight_fragmentation: int = Field(
        default=10, ge=0, description="Points for transaction fragmentation."
    )
    graph_cap: int = Field(
        default=20, ge=0, description="Category cap for graph structure indicators."
    )

    # Final score cap
    final_score_cap: int = Field(
        default=100, ge=0, description="Absolute maximum risk score."
    )

    # Detection thresholds
    rapid_hop_threshold: int = Field(
        default=5, ge=1, description="Minimum hop count for rapid movement detection."
    )
    graph_complexity_edge_threshold: int = Field(
        default=10, ge=1, description="Minimum edge count for high complexity detection."
    )
    graph_fragmentation_tx_threshold: int = Field(
        default=5, ge=1, description="Minimum distinct tx hashes for fragmentation detection."
    )

    model_config = {"frozen": True}