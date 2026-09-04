"""Deterministic KPI helpers for monitoring aggregates."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime


def duration_ms(
    started: datetime | None,
    completed: datetime | None,
) -> float | None:
    """Return elapsed milliseconds when both timestamps exist."""

    if started is None or completed is None:
        return None
    delta = (completed - started).total_seconds() * 1000.0
    if delta < 0:
        return None
    return round(delta, 3)


def average(values: Sequence[float]) -> float | None:
    """Return arithmetic mean or None when empty."""

    if not values:
        return None
    return round(sum(values) / len(values), 3)


def percentile_95(values: Sequence[float]) -> float | None:
    """Return nearest-rank 95th percentile with deterministic ordering."""

    if not values:
        return None
    ordered = sorted(float(item) for item in values)
    # Nearest-rank: ceil(p * n), then convert to 0-based index.
    rank = max(1, min(len(ordered), math.ceil(0.95 * len(ordered))))
    return round(ordered[rank - 1], 3)


def rate(numerator: int, denominator: int) -> float:
    """Return a rounded ratio; empty denominator yields 0.0."""

    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def status_value(status: object) -> str:
    """Normalize enum/string status to a lowercase token."""

    if hasattr(status, "value"):
        return str(status.value).lower()
    return str(status).lower()
