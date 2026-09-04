"""Priority ranking for hypotheses, gaps, and recommendations."""

from __future__ import annotations

from backend.app.investigation_intelligence.models import (
    GapSeverity,
    PriorityLevel,
)
from backend.app.investigation_intelligence.policy import PRIORITY_THRESHOLDS


def priority_from_score(score: float) -> PriorityLevel:
    if score >= PRIORITY_THRESHOLDS["HIGH"]:
        return PriorityLevel.HIGH
    if score >= PRIORITY_THRESHOLDS["MEDIUM"]:
        return PriorityLevel.MEDIUM
    return PriorityLevel.LOW


def priority_from_severity(severity: GapSeverity) -> PriorityLevel:
    if severity == GapSeverity.HIGH:
        return PriorityLevel.HIGH
    if severity == GapSeverity.MEDIUM:
        return PriorityLevel.MEDIUM
    return PriorityLevel.LOW


def rank_priority_value(priority: PriorityLevel) -> int:
    """Lower is higher priority for deterministic sort."""

    order = {
        PriorityLevel.HIGH: 0,
        PriorityLevel.MEDIUM: 1,
        PriorityLevel.LOW: 2,
    }
    return order[priority]
