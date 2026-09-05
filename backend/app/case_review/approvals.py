"""Approval decision helpers (never auto-approve)."""

from __future__ import annotations

from backend.app.case_review.models import ApprovalDecision


def normalize_approval_decision(value: str) -> str:
    normalized = value.strip().upper()
    allowed = {item.value for item in ApprovalDecision}
    if normalized not in allowed:
        raise ValueError(f"Unsupported approval decision: {value}")
    return normalized


def approval_completion(approved_roles: set[str], required: list[str]) -> float:
    if not required:
        return 0.0
    done = sum(1 for role in required if role in approved_roles)
    return round(done / len(required), 4)
