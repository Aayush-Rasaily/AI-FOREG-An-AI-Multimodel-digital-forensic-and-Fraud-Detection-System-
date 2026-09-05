"""Deterministic scoring for tasks and review-queue ordering."""

from __future__ import annotations

from backend.app.decision_support.models import PriorityLevel
from backend.app.decision_support.policy import PRIORITY_THRESHOLDS, TASK_BASE_PRIORITY


def priority_from_score(score: float) -> PriorityLevel:
    if score >= PRIORITY_THRESHOLDS["HIGH"]:
        return PriorityLevel.HIGH
    if score >= PRIORITY_THRESHOLDS["MEDIUM"]:
        return PriorityLevel.MEDIUM
    return PriorityLevel.LOW


def task_priority_score(
    task_type: str,
    *,
    severity_boost: float = 0.0,
    support_count: int = 1,
) -> float:
    base = TASK_BASE_PRIORITY.get(task_type, 0.5)
    boost = min(0.12, max(0, support_count - 1) * 0.03) + min(0.15, severity_boost)
    return round(max(0.0, min(1.0, base + boost)), 4)


def review_priority_score(reason_weights: list[float]) -> float:
    if not reason_weights:
        return 0.0
    return round(max(0.0, min(1.0, sum(reason_weights) / len(reason_weights))), 4)
