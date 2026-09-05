"""API schemas for Phase 9F integrity monitoring."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class IntegrityMetricsResponse(BaseModel):
    checks_total: int
    checks_passed: int
    checks_failed: int
    checks_warned: int
    alert_count: int
    drift_count: int
    evidence_coverage_pct: float
    integrity_score: float
    critical_alerts: int
    high_alerts: int


class IntegrityCheckResponse(BaseModel):
    id: UUID | None = None
    run_id: UUID | None = None
    case_id: UUID | None = None
    check_key: str
    check_code: str
    title: str
    status: str
    severity: str
    evidence_id: str | None = None
    message: str
    expected: str | None = None
    observed: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class IntegrityAlertResponse(BaseModel):
    id: UUID | None = None
    run_id: UUID | None = None
    case_id: UUID | None = None
    alert_key: str
    alert_code: str
    severity: str
    title: str
    message: str
    evidence_id: str | None = None
    check_code: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class IntegrityDriftResponse(BaseModel):
    id: UUID | None = None
    run_id: UUID | None = None
    case_id: UUID | None = None
    drift_key: str
    evidence_id: str
    field_name: str
    previous_value: str | None = None
    current_value: str | None = None
    message: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class IntegrityRunResponse(BaseModel):
    id: UUID | None = None
    case_id: UUID
    status: str
    check_count: int
    alert_count: int
    drift_count: int
    metrics: IntegrityMetricsResponse
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    fingerprints: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    engine_version: str
    policy_version: str
    created_at: datetime | None = None
    completed_at: datetime | None = None
    checks: list[IntegrityCheckResponse] = Field(default_factory=list)
    alerts: list[IntegrityAlertResponse] = Field(default_factory=list)
    drifts: list[IntegrityDriftResponse] = Field(default_factory=list)
    persisted: bool = True


class IntegrityPreviewResponse(IntegrityRunResponse):
    persisted: bool = False


class IntegrityAlertListResponse(BaseModel):
    items: list[IntegrityAlertResponse]
    total: int


class IntegrityDriftListResponse(BaseModel):
    items: list[IntegrityDriftResponse]
    total: int


class IntegrityHistoryItem(BaseModel):
    id: UUID
    case_id: UUID
    status: str
    check_count: int
    alert_count: int
    drift_count: int
    metrics: IntegrityMetricsResponse
    engine_version: str
    policy_version: str
    created_at: datetime
    completed_at: datetime | None = None


class IntegrityHistoryResponse(BaseModel):
    items: list[IntegrityHistoryItem]
    total: int
