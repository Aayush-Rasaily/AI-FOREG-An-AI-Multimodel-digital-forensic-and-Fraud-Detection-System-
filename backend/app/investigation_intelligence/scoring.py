"""Deterministic scoring for hypotheses and overall investigation score."""

from __future__ import annotations

from backend.app.investigation_intelligence.policy import (
    CONTRADICT_PENALTY,
    CONTRADICT_PENALTY_CAP,
    HYPOTHESIS_BASE_CONFIDENCE,
    PROVENANCE_BOOST,
    PROVENANCE_BOOST_CAP,
    SUPPORT_BOOST,
    SUPPORT_BOOST_CAP,
)


def score_hypothesis(
    hypothesis_type: str,
    *,
    support_count: int,
    contradict_count: int,
    provenance_count: int,
) -> float:
    """Return clamped confidence in [0, 1]."""

    base = HYPOTHESIS_BASE_CONFIDENCE.get(hypothesis_type, 0.5)
    support = min(SUPPORT_BOOST_CAP, max(0, support_count - 1) * SUPPORT_BOOST)
    contradict = min(
        CONTRADICT_PENALTY_CAP,
        max(0, contradict_count) * CONTRADICT_PENALTY,
    )
    provenance = min(
        PROVENANCE_BOOST_CAP,
        max(0, provenance_count - 1) * PROVENANCE_BOOST,
    )
    return round(max(0.0, min(1.0, base + support + provenance - contradict)), 4)


def investigation_score(
    *,
    overall_completeness: float,
    open_conflicts: int,
    high_priority_gaps: int,
    hypothesis_count: int,
) -> float:
    """Deterministic case investigation score in [0, 100]."""

    conflict_penalty = min(25.0, open_conflicts * 5.0)
    gap_penalty = min(20.0, high_priority_gaps * 4.0)
    hypothesis_bonus = min(10.0, hypothesis_count * 0.5)
    raw = (overall_completeness * 100.0) - conflict_penalty - gap_penalty
    raw += hypothesis_bonus * 0.2
    return round(max(0.0, min(100.0, raw)), 2)
