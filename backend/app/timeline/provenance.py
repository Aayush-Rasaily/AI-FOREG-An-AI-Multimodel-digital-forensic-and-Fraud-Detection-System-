"""Provenance helpers for timeline events."""

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
