"""Audit framework domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AuditCategory(StrEnum):
    """Top-level audit event categories."""

    CASE = "case"
    EVIDENCE = "evidence"
    ANALYSIS = "analysis"
    REPORT = "report"
    USER = "user"
    SYSTEM = "system"


class IntegrityStatus(StrEnum):
    """Integrity verification result."""

    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class IntegrityResult:
    """One integrity check outcome."""

    target_type: str
    target_id: str
    status: IntegrityStatus
    expected_hash: str | None = None
    computed_hash: str | None = None
    detail: str = ""


@dataclass(frozen=True, slots=True)
class ComplianceCheck:
    """One compliance standard mapping."""

    standard: str
    clause: str
    description: str
    satisfied: bool
    detail: str = ""


@dataclass(frozen=True, slots=True)
class AuditExportResult:
    """Packaged audit log export."""

    format: str
    total_events: int
    payload: bytes
    checksum: str
    metadata: dict[str, Any] = field(default_factory=dict)
