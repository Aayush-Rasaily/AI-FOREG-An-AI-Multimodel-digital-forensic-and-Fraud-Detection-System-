"""Domain models for forensic investigation reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ReportStatus(StrEnum):
    """Lifecycle for one forensic report generation run."""

    QUEUED = "QUEUED"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ReportResult:
    """Outcome of report generation."""

    status: ReportStatus
    content: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message_safe: str | None = None
