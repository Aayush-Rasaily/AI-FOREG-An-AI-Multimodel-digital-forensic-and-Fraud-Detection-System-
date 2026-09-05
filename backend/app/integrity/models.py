"""In-memory domain models for Phase 9F integrity monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class CheckStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"
    INFO = "INFO"


class AlertSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass(frozen=True)
class ProvenanceBundle:
    evidence_ids: tuple[str, ...] = ()
    custody_event_ids: tuple[str, ...] = ()
    audit_event_ids: tuple[str, ...] = ()
    report_ids: tuple[str, ...] = ()
    storage_keys: tuple[str, ...] = ()
    detail: str | None = None


@dataclass
class CheckDraft:
    check_key: str
    check_code: str
    title: str
    status: CheckStatus
    severity: AlertSeverity
    evidence_id: str | None
    message: str
    expected: str | None = None
    observed: str | None = None
    provenance: ProvenanceBundle = field(default_factory=ProvenanceBundle)


@dataclass
class AlertDraft:
    alert_key: str
    alert_code: str
    severity: AlertSeverity
    title: str
    message: str
    evidence_id: str | None = None
    check_code: str | None = None
    provenance: ProvenanceBundle = field(default_factory=ProvenanceBundle)


@dataclass
class DriftDraft:
    drift_key: str
    evidence_id: str
    field_name: str
    previous_value: str | None
    current_value: str | None
    message: str
    provenance: ProvenanceBundle = field(default_factory=ProvenanceBundle)


@dataclass
class IntegrityMetrics:
    checks_total: int = 0
    checks_passed: int = 0
    checks_failed: int = 0
    checks_warned: int = 0
    alert_count: int = 0
    drift_count: int = 0
    evidence_coverage_pct: float = 0.0
    integrity_score: float = 0.0
    critical_alerts: int = 0
    high_alerts: int = 0


@dataclass
class IntegrityPlan:
    status: RunStatus
    metrics: IntegrityMetrics
    checks: list[CheckDraft]
    alerts: list[AlertDraft]
    drifts: list[DriftDraft]
    timeline: list[dict[str, Any]]
    provenance: dict[str, Any]
