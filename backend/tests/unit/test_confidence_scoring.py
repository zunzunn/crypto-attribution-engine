"""Confidence scoring unit tests for scoring_model_v0.

Verifies the transparent weighted-factor formula: base exact-match score, hop
penalty, corroboration bonus, tag freshness, zero-value/time-continuity
penalties, clamping, tier mapping, and factor explainability. All deterministic.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas.graph import GraphEdge
from app.services.attribution.scoring import ConfidenceScorer
from tests.factories import eth_addr, make_edge

NOW = datetime(2026, 6, 1, tzinfo=timezone.utc)
SCORER = ConfidenceScorer(now=NOW)

VASP = eth_addr(100)


def r4(value: float) -> float:
    return round(value, 4)



def graph_edge(*, index: int = 1, value: str = "1000", ts: datetime | None = None) -> GraphEdge:
    return make_edge(
        index,
        eth_addr(index + 10),
        VASP,
        value=value,
        block_timestamp=ts or (NOW - timedelta(days=1)),
        block_number=index,
    )


def score(hop_count=1, n_evidence=1, imported_at=None, path_edges=None, now=NOW):
    return ConfidenceScorer(now=now).score(
        hop_count=hop_count,
        evidence_tx_hashes=[f"0x{h:064x}" for h in range(1, n_evidence + 1)],
        imported_at=imported_at,
        path_edges=path_edges or [graph_edge()],
    )


class TestBase:
    def test_direct_fresh_match_high(self) -> None:
        result = score(imported_at=NOW - timedelta(days=5))
        assert result.base_score == 0.80
        assert result.score == r4(0.85)
        assert result.tier == "high"
        names = {f.name for f in result.factors}
        assert "tag_freshness" in names

    def test_default_imported_none_is_neutral(self) -> None:
        result = score(imported_at=None)
        assert result.score == r4(0.80)
        assert result.tier == "high"


class TestHopDistance:
    def test_hop_penalty_increases_with_depth(self) -> None:
        one = score(hop_count=1, imported_at=None)
        three = score(hop_count=3, imported_at=None)
        assert one.score > three.score
        factor = next(f for f in three.factors if f.name == "hop_distance")
        assert factor.delta == -0.06

    def test_hop_penalty_is_capped(self) -> None:
        many = score(hop_count=12, imported_at=None)
        factor = next(f for f in many.factors if f.name == "hop_distance")
        assert factor.delta == -0.15


class TestCorroboration:
    def test_additional_evidence_txs_add_bonus(self) -> None:
        single = score(hop_count=1, n_evidence=1, imported_at=None)
        multi = score(hop_count=1, n_evidence=4, imported_at=None)
        factor = next(f for f in multi.factors if f.name == "corroboration")
        assert factor.delta == 0.10
        assert multi.score == r4(single.score + 0.10)

    def test_corroboration_bonus_caps_at_two_extra(self) -> None:
        ten = score(hop_count=1, n_evidence=10, imported_at=None)
        factor = next(f for f in ten.factors if f.name == "corroboration")
        assert factor.delta == 0.10


class TestTagFreshness:
    def test_fresh_tag_positive(self) -> None:
        result = score(imported_at=NOW - timedelta(days=10))
        factor = next(f for f in result.factors if f.name == "tag_freshness")
        assert factor.delta == 0.05

    def test_stale_tag_negative(self) -> None:
        result = score(imported_at=NOW - timedelta(days=200))
        factor = next(f for f in result.factors if f.name == "tag_freshness")
        assert factor.delta == -0.10

    def test_mid_age_neutral(self) -> None:
        result = score(imported_at=NOW - timedelta(days=90))
        assert all(f.name != "tag_freshness" for f in result.factors)


class TestEvidenceStrength:
    def test_zero_value_hop_penalty(self) -> None:
        zero_edge = graph_edge(value="0")
        result = score(path_edges=[zero_edge], imported_at=None)
        factor = next(f for f in result.factors if f.name == "zero_value_hop")
        assert factor.delta == -0.05

    def test_time_regression_penalty(self) -> None:
        regression = [
            graph_edge(index=1, ts=NOW - timedelta(days=3)),
            graph_edge(index=2, ts=NOW - timedelta(days=4)),
        ]
        result = score(path_edges=regression, imported_at=None)
        factor = next(f for f in result.factors if f.name == "time_discontinuity")
        assert factor.delta == -0.05

    def test_monotonic_timestamps_no_penalty(self) -> None:
        ordered = [
            graph_edge(index=1, ts=NOW - timedelta(days=4)),
            graph_edge(index=2, ts=NOW - timedelta(days=3)),
        ]
        result = score(path_edges=ordered, imported_at=None)
        assert all(f.name != "time_discontinuity" for f in result.factors)


class TestBoundsAndTiers:
    def test_score_stays_within_bounds(self) -> None:
        worst = score(
            hop_count=12,
            n_evidence=1,
            imported_at=NOW - timedelta(days=400),
            path_edges=[
                graph_edge(index=1, value="0"),
                graph_edge(index=2, value="0", ts=NOW - timedelta(days=5)),
            ],
        )
        assert 0.0 <= worst.score <= 1.0
        assert worst.score == r4(0.80 - 0.15 - 0.10 - 0.10)  # hop+stale+zero

    def test_tier_boundaries(self) -> None:
        assert SCORER._tier(0.75) == "high"
        assert SCORER._tier(0.74) == "medium"
        assert SCORER._tier(0.45) == "medium"
        assert SCORER._tier(0.44) == "low"
        assert SCORER._tier(0.15) == "low"
        assert SCORER._tier(0.14) == "very_low"

    def test_result_is_explainable(self) -> None:
        result = score(hop_count=3, n_evidence=3, imported_at=NOW - timedelta(days=5))
        assert result.scoring_model_version == "scoring_model_v0"
        assert result.factors
        for factor in result.factors:
            assert factor.name
            assert factor.reason
            assert isinstance(factor.delta, float)
