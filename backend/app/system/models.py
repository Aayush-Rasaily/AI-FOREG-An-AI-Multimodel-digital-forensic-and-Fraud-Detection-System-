"""Domain models for system monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DiagnosticStatus(StrEnum):
    """Result of one diagnostic check."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


class ServiceStatus(StrEnum):
    """Health of one service dependency."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True, slots=True)
class DiagnosticCheckResult:
    """One diagnostic check outcome."""

    name: str
    status: DiagnosticStatus
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class JobCategorySummary:
    """Job counts for one pipeline category."""

    category: str
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
