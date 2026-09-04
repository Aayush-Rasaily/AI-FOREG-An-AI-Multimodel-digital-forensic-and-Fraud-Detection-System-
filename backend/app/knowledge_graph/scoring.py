"""Deterministic relationship scoring."""

from __future__ import annotations

from backend.app.knowledge_graph.policy import (
    PROVENANCE_BOOST,
    PROVENANCE_BOOST_CAP,
    RELATIONSHIP_BASE_WEIGHT,
    SUPPORT_BOOST,
    SUPPORT_BOOST_CAP,
)


def score_relationship(
    *,
    relationship_type: str,
    support_count: int,
    provenance_count: int,
    base_confidence: float | None = None,
) -> tuple[float, float]:
    """Return (confidence, relationship_weight) with deterministic boosts."""

    weight = RELATIONSHIP_BASE_WEIGHT.get(relationship_type, 0.70)
    confidence = base_confidence if base_confidence is not None else weight
    support_extra = min(SUPPORT_BOOST_CAP, max(0, support_count - 1) * SUPPORT_BOOST)
    prov_extra = min(
        PROVENANCE_BOOST_CAP,
        max(0, provenance_count - 1) * PROVENANCE_BOOST,
    )
    confidence = min(1.0, round(confidence + support_extra + prov_extra, 4))
    weight = min(1.0, round(weight + support_extra * 0.5, 4))
    return confidence, weight
