"""Domain models for platform validation (non-ORM)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class CheckStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class ReadinessLevel(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    NOT_READY = "NOT_READY"


@dataclass(frozen=True)
class CheckOutcome:
    key: str
    category: str
    label: str
    status: CheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationPlan:
    outcomes: tuple[CheckOutcome, ...]
    readiness_score: float
    readiness_level: ReadinessLevel
    provenance: dict[str, Any]
    health_report: dict[str, Any]
    compatibility: dict[str, Any]
