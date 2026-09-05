"""In-memory domain models for Phase 9G analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class MetricPoint:
    key: str
    label: str
    value: float
    unit: str = "count"
    category: str = "overview"
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsPlan:
    status: RunStatus
    metrics: list[MetricPoint]
    sections: dict[str, dict[str, Any]]
    trends: dict[str, list[dict[str, Any]]]
    provenance: dict[str, Any]
    dashboard: dict[str, Any]
