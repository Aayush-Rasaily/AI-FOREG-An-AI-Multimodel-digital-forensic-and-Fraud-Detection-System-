"""Decision log helpers (persist investigator decisions only)."""

from __future__ import annotations

from backend.app.decision_support.models import DecisionType

ALLOWED_DECISIONS = frozenset(item.value for item in DecisionType)


def normalize_decision_type(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in ALLOWED_DECISIONS:
        raise ValueError(f"Unsupported decision type: {value}")
    return normalized
