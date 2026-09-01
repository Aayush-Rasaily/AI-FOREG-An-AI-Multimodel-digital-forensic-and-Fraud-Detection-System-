"""Shared preprocessing helpers."""

from __future__ import annotations

from typing import Any


def ensure_batch(items: list[Any]) -> list[Any]:
    """Wrap a single item into a batch when needed."""

    if not items:
        return []
    return items


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value to a range."""

    return max(minimum, min(maximum, value))
