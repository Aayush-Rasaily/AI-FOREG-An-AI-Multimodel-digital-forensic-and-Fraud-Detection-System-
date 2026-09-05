"""Approval role helpers for case review."""

from __future__ import annotations

from backend.app.case_review.models import ApproverRole
from backend.app.case_review.policy import REQUIRED_APPROVER_ROLES


def required_roles() -> list[str]:
    return list(REQUIRED_APPROVER_ROLES)


def normalize_approver_role(value: str) -> str:
    normalized = value.strip().upper()
    allowed = {item.value for item in ApproverRole}
    if normalized not in allowed:
        raise ValueError(f"Unsupported approver role: {value}")
    return normalized
