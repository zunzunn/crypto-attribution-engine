"""Rule-based behavior risk scoring (Risk Scoring v1).

Risk score answers ``how suspicious are the observed transaction behaviors?``
completely separate from attribution confidence (which answers ``how confident
are we in the VASP/entity attribution?``).

The model is a transparent weighted-factor formula - no ML. Every output carries
its factor breakdown for explainability. Weights, thresholds, and category caps
are configurable via ``RiskScoringConfig``.

Risk levels:
  0--24: LOW
  25--49: MEDIUM
  50--74: HIGH
  75--100: CRITICAL
"""

from __future__ import annotations

from datetime import datetime

from app.schemas.risk import RiskAssessment, RiskIndicator, RiskLevel, RiskScoringConfig


# --------------------------------------------------------------------------- #
# Detection rules applied to the traversal / attribution pipeline output
# --------------------------------------------------------------------------- #


def _extract_addresses_from_entities(entities: list) -> list[str]:
    """Extract address strings from entity match objects."""
    addrs: list[str] = []
    for ent in entities:
        # ent is an EntityMatch; the actual Entity is at ent.entity
        if hasattr(ent, "entity") and ent.entity is not None:
            domain_ent = ent.entity
        else:
            domain_ent = ent
        if hasattr(domain_ent, "address"):
            addrs.append(domain_ent.address)
        elif hasattr(domain_ent, "matched_address"):
            addrs.append(domain_ent.matched_address)
    return addrs


def _extract_tx_hashes_from_hops(hops: list) -> list[str]:
    """Extract transaction hashes from EvidenceHop objects."""
    hashes: list[str] = []
    for hop in hops:
        if hasattr(hop, "edge") and hasattr(hop.edge, "tx_hash"):
            hashes.append(hop.edge.tx_hash)
    return hashes


def _extract_addresses_from_hops(hops: list) -> list[str]:
    """Extract addresses from EvidenceHop objects."""
    addrs: list[str] = []
    for hop in hops:
        if hasattr(hop, "edge") and hasattr(hop.edge, "from_address"):
            addrs.append(hop.edge.from_address)
        if hasattr(hop, "edge") and hasattr(hop.edge, "to_address"):
            addrs.append(hop.edge.to_address)
    return addrs


def _extract_addresses_from_traversal(traversal_result: object) -> list[str]:
    """Extract discovered addresses from traversal result."""
    addrs: list[str] = []
    discovered = getattr(traversal_result, "discovered_addresses", [])
    addrs.extend(discovered)
    return addrs


def _extract_tx_hashes_from_traversal(traversal_result: object) -> list[str]:
    """Extract transaction hashes from traversal result."""
    hashes: list[str] = []
    edges = getattr(traversal_result, "edges_examined", [])
    for edge in edges:
        if hasattr(edge, "tx_hash"):
            hashes.append(edge.tx_hash)
    # Also from paths
    if not hashes and hasattr(traversal_result, "paths"):
        for path in traversal_result.paths:
            if hasattr(path, "hops"):
                for hop in path.hops:
                    if hasattr(hop, "edge") and hasattr(hop.edge, "tx_hash"):
                        hashes.append(hop.edge.tx_hash)
    return hashes


def _detect_entity_risk_indicators(
    *,
    config: RiskScoringConfig,
    matched_entities: list,
) -> tuple[list[RiskIndicator], int]:
    """Detect entity-risk indicators based on matched entity categories.

    Checks whether any addresses encountered during traversal are tagged with
    high-risk entity categories (sanctions, ransomware, fraud, darknet).

    Returns (indicators, total_entity_risk_points) where indicators is the
    subset that falls within the entity_risk_cap.
    """
    indicators: list[RiskIndicator] = []
    entity_risk_points = 0

    # Collect applicable entity-risk weights with their labels
    entity_weights: list[tuple[int, str]] = []
    if config.entity_risk_weight_sanctions > 0:
        entity_weights.append((config.entity_risk_weight_sanctions, "sanctions"))
    if config.entity_risk_weight_ransomware > 0:
        entity_weights.append(
            (config.entity_risk_weight_ransomware, "ransomware")
        )
    if config.entity_risk_weight_fraud > 0:
        entity_weights.append((config.entity_risk_weight_fraud, "fraud"))
    if config.entity_risk_weight_darknet > 0:
        entity_weights.append(
            (config.entity_risk_weight_darknet, "darknet")
        )

    # Find which labels have matches among the matched entities
    labels_with_matches: dict[str, int] = {}  # label -> points
    for weight, label in entity_weights:
        for entity_match in matched_entities:
            # entity_match is an EntityMatch; its .entity is the Entity
            cat = entity_match.entity.category.value if hasattr(entity_match, "entity") and entity_match.entity else None
            if cat == label:
                labels_with_matches[label] = weight
                break  # one match per label is enough

    # Build indicators respecting the entity_risk_cap
    # We only count the highest applicable weight (cap enforcement)
    if labels_with_matches:
        # Sort labels by weight descending
        sorted_labels = sorted(
            labels_with_matches.items(), key=lambda x: x[1], reverse=True
        )
        for label, weight in sorted_labels:
            if entity_risk_points + weight <= config.entity_risk_cap:
                # Find the entity to get supporting info
                matched_entity = next(
                    e for e in matched_entities if e.category.value == label
                )
                explanation = (
                    f"Entity matched with high-risk category: {label}."
                )
                indicators.append(
                    RiskIndicator(
                        indicator_type=label,
                        points=weight,
                        explanation=explanation,
                        supporting_addresses=_extract_addresses_from_entities(
                            [matched_entity]
                        ),
                        supporting_tx_hashes=[],
                        evidence={
                            "entity_category": matched_entity.category.value,
                            "entity_name": matched_entity.name,
                            "tag_source": matched_entity.tag_source,
                            "tag_version": matched_entity.tag_version,
                        },
                    )
                )
                entity_risk_points += weight
            # If adding this weight would exceed the cap, we stop counting
            # further entity risk indicators (the cap limits the category total)

    return indicators, entity_risk_points


def _detect_mixer_interaction(
    *,
    config: RiskScoringConfig,
    matched_entities: list,
) -> tuple[list[RiskIndicator], int]:
    """Detect mixer interaction: any matched entity with category MIXER."""

    indicators: list[RiskIndicator] = []
    mixer_points = 0

    for entity_match in matched_entities:
        # entity_match is an EntityMatch; its .entity is the Entity
        cat = entity_match.entity.category.value if hasattr(entity_match, "entity") and entity_match.entity else None
        if cat == "MIXER":
            explanation = (
                f"Mixer entity interaction detected: {entity_match.entity.name or 'unnamed mixer'}."
            )
            indicators.append(
                RiskIndicator(
                    indicator_type="mixer",
                    points=config.behavioral_weight_mixer,
                    explanation=explanation,
                    supporting_addresses=[
                        entity_match.address
                        if hasattr(entity_match, "address")
                        else "unknown"
                    ],
                    supporting_tx_hashes=[],
                    evidence={
                        "entity_category": entity_match.entity.category.value,
                        "entity_name": entity_match.entity.name,
                        "tag_source": entity_match.entity.tag_source,
                        "tag_version": entity_match.entity.tag_version,
                    },
                )
            )
            mixer_points = config.behavioral_weight_mixer
            break  # one mixer match is enough; cap enforced at category level

    return indicators, mixer_points


def _detect_rapid_movement(
    *,
    config: RiskScoringConfig,
    hop_count: int,
) -> tuple[list[RiskIndicator], int]:
    """Detect rapid multi-hop movement indicator."""

    indicators: list[RiskIndicator] = []
    points = 0

    if hop_count >= config.rapid_hop_threshold:
        explanation = (
            f"Rapid multi-hop movement detected: {hop_count} hops "
            f"(threshold: {config.rapid_hop_threshold})."
        )
        indicators.append(
            RiskIndicator(
                indicator_type="rapid_movement",
                points=config.behavioral_weight_rapid_hop,
                explanation=explanation,
                supporting_addresses=[],
                supporting_tx_hashes=[],
                evidence={
                    "hop_count": hop_count,
                    "threshold": config.rapid_hop_threshold,
                },
            )
        )
        points = config.behavioral_weight_rapid_hop

    return indicators, points


def _detect_graph_complexity(
    *,
    config: RiskScoringConfig,
    traversal_result: object,
) -> tuple[list[RiskIndicator], int]:
    """Detect high graph complexity indicator."""

    indicators: list[RiskIndicator] = []
    points = 0

    num_edges = getattr(traversal_result, "edges_examined", 0)
    num_addresses = getattr(traversal_result, "addresses_discovered", 0)

    if num_edges >= config.graph_complexity_edge_threshold:
        explanation = (
            f"High graph complexity detected: {num_edges} edges examined "
            f"(threshold: {config.graph_complexity_edge_threshold})."
        )
        indicators.append(
            RiskIndicator(
                indicator_type="high_complexity",
                points=config.graph_weight_complexity,
                explanation=explanation,
                supporting_addresses=_extract_addresses_from_traversal(
                    traversal_result
                ),
                supporting_tx_hashes=_extract_tx_hashes_from_traversal(
                    traversal_result
                ),
                evidence={
                    "edges_examined": num_edges,
                    "addresses_discovered": num_addresses,
                    "threshold": config.graph_complexity_edge_threshold,
                },
            )
        )
        points = config.graph_weight_complexity

    return indicators, points


def _detect_transaction_fragmentation(
    *,
    config: RiskScoringConfig,
    traversal_result: object,
) -> tuple[list[RiskIndicator], int]:
    """Detect transaction fragmentation indicator."""

    indicators: list[RiskIndicator] = []
    points = 0

    # Count distinct transaction hashes supporting the path(s)
    distinct_tx_hashes: set[str] = set()

    # From paths (each hop has an edge with a tx_hash)
    if hasattr(traversal_result, "paths"):
        for path in traversal_result.paths:
            if hasattr(path, "hops"):
                for hop in path.hops:
                    if hasattr(hop, "edge") and hasattr(hop.edge, "tx_hash"):
                        distinct_tx_hashes.add(hop.edge.tx_hash)

    if len(distinct_tx_hashes) >= config.graph_fragmentation_tx_threshold:
        explanation = (
            f"Transaction fragmentation detected: {len(distinct_tx_hashes)} distinct "
            f"transaction hashes (threshold: {config.graph_fragmentation_tx_threshold})."
        )
        indicators.append(
            RiskIndicator(
                indicator_type="fragmentation",
                points=config.graph_weight_fragmentation,
                explanation=explanation,
                supporting_addresses=_extract_addresses_from_traversal(
                    traversal_result
                ),
                supporting_tx_hashes=list(distinct_tx_hashes),
                evidence={
                    "distinct_tx_hashes": len(distinct_tx_hashes),
                    "threshold": config.graph_fragmentation_tx_threshold,
                    "paths_count": len(traversal_result.paths),
                },
            )
        )
        points = config.graph_weight_fragmentation

    return indicators, points


def _detect_cross_chain_movement_deferred(
    **_kwargs: object,
) -> tuple[list[RiskIndicator], int]:
    """Cross-chain movement detection - deliberately deferred.

    Not supported by the current data model (no cross-chain correlation).
    Returns empty indicators and 0 points so as not to falsely trigger.
    """
    return [], 0


def assess_risk(
    *,
    config: RiskScoringConfig,
    matched_entities: list,
    hop_count: int,
    path_edges: list,
    traversal_result: object,
) -> RiskAssessment:
    """Run the full risk-scoring pipeline and return a RiskAssessment."""

    all_indicators: list[RiskIndicator] = []
    category_points: dict[str, int] = {
        "entity_risk": 0,
        "behavioral": 0,
        "graph_structure": 0,
    }

    # 1. Entity risk indicators (sanctions, ransomware, fraud, darknet)
    entity_indicators, entity_points = _detect_entity_risk_indicators(
        config=config, matched_entities=matched_entities
    )
    all_indicators.extend(entity_indicators)
    category_points["entity_risk"] = entity_points

    # 2. Mixer interaction (behavioral)
    mixer_indicators, mixer_points = _detect_mixer_interaction(
        config=config, matched_entities=matched_entities
    )
    all_indicators.extend(mixer_indicators)
    category_points["behavioral"] += mixer_points

    # 3. Rapid movement (behavioral)
    rapid_indicators, rapid_points = _detect_rapid_movement(
        config=config, hop_count=hop_count
    )
    all_indicators.extend(rapid_indicators)
    category_points["behavioral"] += rapid_points

    # 4. Graph structure indicators (complexity, fragmentation)
    graph_complexity_indicators, complexity_points = _detect_graph_complexity(
        config=config, traversal_result=traversal_result
    )
    all_indicators.extend(graph_complexity_indicators)
    category_points["graph_structure"] += complexity_points

    graph_fragmentation_indicators, fragmentation_points = (
        _detect_transaction_fragmentation(
            config=config, traversal_result=traversal_result
        )
    )
    all_indicators.extend(graph_fragmentation_indicators)
    category_points["graph_structure"] += fragmentation_points

    # 5. Cross-chain movement (deferred - explicitly NOT triggered)
    # Do not add any indicators or points for cross-chain; the abstraction
    # ensures this indicator never fires with current data.

    # ------------------------------------------------------------------ #
    # Apply category caps and compute final score
    # ------------------------------------------------------------------ #

    # Enforce entity_risk_cap (already handled in _detect_entity_risk_indicators,
    # but double-check here)
    entity_risk_points = min(category_points["entity_risk"], config.entity_risk_cap)
    category_points["entity_risk"] = entity_risk_points

    # Enforce behavioral_cap: sum behavioral points and cap
    behavioral_total = category_points["behavioral"]
    behavioral_capped = min(behavioral_total, config.behavioral_cap)
    category_points["behavioral"] = behavioral_capped

    # Enforce graph_cap: sum graph points and cap
    graph_total = category_points["graph_structure"]
    graph_capped = min(graph_total, config.graph_cap)
    category_points["graph_structure"] = graph_capped

    # Total score = sum of category points, capped at final_score_cap
    total_score = (
        entity_risk_points + behavioral_capped + graph_capped
    )
    total_score = min(total_score, config.final_score_cap)

    # Determine risk level
    if total_score >= 75:
        risk_level = RiskLevel.CRITICAL
    elif total_score >= 50:
        risk_level = RiskLevel.HIGH
    elif total_score >= 25:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW

    # Build the final indicator list respecting category caps
    # Filter indicators to only those that contributed within caps
    final_indicators: list[RiskIndicator] = []

    # Select entity risk indicators that fall within the cap
    for ind in entity_indicators:
        if ind.indicator_type in {"sanctions", "ransomware", "fraud", "darknet"}:
            final_indicators.append(ind)

    # Select mixer indicator
    for ind in mixer_indicators:
        if ind.indicator_type == "mixer":
            final_indicators.append(ind)

    # Select rapid movement indicator
    for ind in rapid_indicators:
        if ind.indicator_type == "rapid_movement":
            final_indicators.append(ind)

    # Select graph complexity indicator
    for ind in graph_complexity_indicators:
        if ind.indicator_type == "high_complexity":
            final_indicators.append(ind)

    # Select fragmentation indicator
    for ind in graph_fragmentation_indicators:
        if ind.indicator_type == "fragmentation":
            final_indicators.append(ind)

    # Build category breakdown dict (only include non-zero categories)
    category_breakdown: dict[str, int] = {}
    if category_points["entity_risk"] > 0:
        category_breakdown["entity_risk"] = category_points["entity_risk"]
    if category_points["behavioral"] > 0:
        category_breakdown["behavioral"] = category_points["behavioral"]
    if category_points["graph_structure"] > 0:
        category_breakdown["graph_structure"] = category_points["graph_structure"]

    return RiskAssessment(
        risk_level=risk_level,
        total_score=total_score,
        indicators=final_indicators,
        category_breakdown=category_breakdown,
    )