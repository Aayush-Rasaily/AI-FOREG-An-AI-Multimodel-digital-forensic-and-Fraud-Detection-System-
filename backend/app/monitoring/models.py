"""Domain enums for operational monitoring."""

from __future__ import annotations

from enum import StrEnum


class PlatformHealthStatus(StrEnum):
    """Deterministic platform health classification."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
