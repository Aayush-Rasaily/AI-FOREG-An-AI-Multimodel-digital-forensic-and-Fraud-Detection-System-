"""API schemas for Phase 9H platform validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ValidationResultResponse(BaseModel):
    check_key: str
    category: str
    label: str
    status: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationIssueResponse(BaseModel):
    check_key: str
    category: str
    severity: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class PlatformValidationRunResponse(BaseModel):
    id: UUID | None = None
    status: str
    readiness_score: float
    readiness_level: str
    check_count: int
    pass_count: int
    warn_count: int
    fail_count: int
    results: list[ValidationResultResponse] = Field(default_factory=list)
    issues: list[ValidationIssueResponse] = Field(default_factory=list)
    health_report: dict[str, Any] = Field(default_factory=dict)
    compatibility: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    engine_version: str
    policy_version: str
    created_at: datetime | None = None
    completed_at: datetime | None = None
    persisted: bool = True


class ReadinessResponse(BaseModel):
    readiness_score: float
    readiness_level: str
    check_count: int
    pass_count: int
    warn_count: int
    fail_count: int
    engine_version: str
    policy_version: str
    generated_at: datetime | None = None
    persisted: bool = False
    run_id: UUID | None = None


class HealthReportResponse(BaseModel):
    report: dict[str, Any]
    engine_version: str
    policy_version: str
    persisted: bool = False
    run_id: UUID | None = None


class ValidationListResponse(BaseModel):
    runs: list[PlatformValidationRunResponse] = Field(default_factory=list)
    engine_version: str
    policy_version: str
