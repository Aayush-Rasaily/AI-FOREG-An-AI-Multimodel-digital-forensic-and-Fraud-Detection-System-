"""Provenance helpers for correlation records."""

from __future__ import annotations

from typing import Any
from uuid import UUID


def build_provenance(**references: UUID | str | None) -> dict[str, Any]:
    """Build a provenance payload from optional upstream references."""

    payload: dict[str, Any] = {}
    for key, value in references.items():
        if value is not None:
            payload[key] = str(value)
    return payload


def canonical_pair(left: UUID, right: UUID) -> tuple[UUID, UUID]:
    """Order evidence IDs so smaller UUID is always left."""

    if str(left) <= str(right):
        return left, right
    return right, left


def correlation_key(
    left: UUID,
    right: UUID,
    correlation_type: str,
) -> str:
    """Deterministic unique key for one pair + type."""

    a, b = canonical_pair(left, right)
    return f"{correlation_type}:{a}:{b}"
