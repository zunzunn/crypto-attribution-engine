"""Rule-based attribution confidence scoring (``scoring_model_v0``).

Confidence here is the *likelihood that a known-address match is correct* given
match type, hop distance, path continuity, and corroborating evidence. It is
strictly separate from criminal/risk scoring, which belongs to Phase 3.

The model is a transparent weighted-factor formula - no ML. Every output score
carries its factor breakdown for explainability.

Formula (v0)
------------
    base = 0.80 (exact known-address match)

    score = base
            + hop_distance       (-0.03 per hop beyond the first, cap -0.15)
            + corroboration      (+0.05 per distinct evidence tx beyond the
                                  first, cap +0.10)
            + tag_freshness      (+0.05 when the registry entry is < 30 days
                                  old; -0.10 when older than 180 days)
            + zero_value_hop     (-0.05 when any hop moved zero native value)
            + time_discontinuity (-0.05 when block timestamps regress along
                                  the path)

    clamped to [0, 1], rounded to 4 decimals, then tiered
    (high >= 0.75, medium >= 0.45, low >= 0.15, very_low < 0.15).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.schemas import ConfidenceFactor, ConfidenceResult
from app.schemas.graph import GraphEdge
from app.utils.time import utc_now

SCORING_MODEL_VERSION = "scoring_model_v0"
BASE_EXACT_MATCH = 0.80

HOP_PENALTY_PER_HOP = 0.03
HOP_PENALTY_CAP = 0.15
CORROBORATION_BONUS_PER_TX = 0.05
CORROBORATION_BONUS_CAP = 0.10
FRESH_WINDOW = timedelta(days=30)
STALE_WINDOW = timedelta(days=180)
ZERO_VALUE_PENALTY = 0.05
TIME_DISCONTINUITY_PENALTY = 0.05


def _age(dt: datetime, now: datetime) -> timedelta:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=now.tzinfo)
    return now - dt


class ConfidenceScorer:
    def __init__(self, *, now: datetime | None = None) -> None:
        # Injectable clock keeps tests deterministic; defaults to real UTC now.
        self._clock: datetime | None = now

    def _now(self) -> datetime:
        return self._clock if self._clock is not None else utc_now()

    def score(
        self,
        *,
        hop_count: int,
        evidence_tx_hashes: list[str],
        imported_at: datetime | None,
        path_edges: list[GraphEdge],
    ) -> ConfidenceResult:
        factors: list[ConfidenceFactor] = []
        score = BASE_EXACT_MATCH

        hops = max(hop_count, 1)
        hop_delta = -min(HOP_PENALTY_PER_HOP * (hops - 1), HOP_PENALTY_CAP)
        score += hop_delta
        if hop_delta:
            factors.append(
                ConfidenceFactor(
                    name="hop_distance",
                    delta=round(hop_delta, 4),
                    reason=f"{hops} hops from the seed",
                )
            )

        n_evidence = len(set(evidence_tx_hashes))
        corr_delta = CORROBORATION_BONUS_PER_TX * min(n_evidence - 1, 2)
        score += corr_delta
        if corr_delta:
            factors.append(
                ConfidenceFactor(
                    name="corroboration",
                    delta=round(corr_delta, 4),
                    reason=f"{n_evidence} distinct transactions supporting the match",
                )
            )

        fresh_delta: float = 0.0
        if imported_at is not None:
            age = _age(imported_at, self._now())
            if age < FRESH_WINDOW:
                fresh_delta = 0.05
            elif age > STALE_WINDOW:
                fresh_delta = -0.10
        score += fresh_delta
        if fresh_delta:
            label = "<30 days" if fresh_delta > 0 else ">180 days"
            factors.append(
                ConfidenceFactor(
                    name="tag_freshness",
                    delta=fresh_delta,
                    reason=f"registry entry {label} old",
                )
            )

        if any(self._is_zero(edge) for edge in path_edges):
            score += -ZERO_VALUE_PENALTY
            factors.append(
                ConfidenceFactor(
                    name="zero_value_hop",
                    delta=-ZERO_VALUE_PENALTY,
                    reason="at least one hop moved zero native value",
                )
            )

        if self._is_time_discontinuous(path_edges):
            score += -TIME_DISCONTINUITY_PENALTY
            factors.append(
                ConfidenceFactor(
                    name="time_discontinuity",
                    delta=-TIME_DISCONTINUITY_PENALTY,
                    reason="block timestamps regress along the path",
                )
            )

        final = round(min(max(score, 0.0), 1.0), 4)
        return ConfidenceResult(
            base_score=round(BASE_EXACT_MATCH, 4),
            score=final,
            tier=self._tier(final),
            scoring_model_version=SCORING_MODEL_VERSION,
            factors=factors,
        )

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _is_zero(edge: GraphEdge) -> bool:
        try:
            return int(edge.value or "0") == 0
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _is_time_discontinuous(path_edges: list[GraphEdge]) -> bool:
        previous: datetime | None = None
        any_seen = False
        for edge in path_edges:
            ts = edge.block_timestamp
            if ts is None:
                continue
            if any_seen and previous is not None and ts < previous:
                return True
            previous = ts
            any_seen = True
        return False

    @staticmethod
    def _tier(score: float) -> str:
        if score >= 0.75:
            return "high"
        if score >= 0.45:
            return "medium"
        if score >= 0.15:
            return "low"
        return "very_low"