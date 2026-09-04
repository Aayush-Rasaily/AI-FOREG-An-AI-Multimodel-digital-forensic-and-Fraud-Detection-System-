"""Domain models for Phase 8F security governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    """One deterministic chain/validation finding."""

    check: str
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Aggregate chain validation outcome."""

    status: str
    findings: list[ValidationFinding]
    generated_at: datetime
    policy_version: str
    engine_version: str


@dataclass(frozen=True, slots=True)
class ComplianceSnapshot:
    """Deterministic compliance summary for a case or platform."""

    status: str
    chain_of_custody_complete: bool
    evidence_integrity_ok: bool
    audit_complete: bool
    workflow_compliant: bool
    report_approval_compliant: bool
    missing_approvals: list[str]
    missing_provenance: list[str]
    policy_violations: list[str]
    details: dict[str, Any]
    generated_at: datetime
    policy_version: str
    engine_version: str
    case_id: UUID | None = None
