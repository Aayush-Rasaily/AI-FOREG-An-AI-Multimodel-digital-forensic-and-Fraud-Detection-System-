"""Pydantic schemas for cross-evidence correlation APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.correlation.models import CorrelationRunStatus, CorrelationType


class CorrelationSupportResponse(BaseModel):
    """One supporting artifact or finding."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    support_kind: str
    support_ref: str
    label: str
    value: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceCorrelationResponse(BaseModel):
    """One cross-evidence correlation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_run_id: UUID
    case_id: UUID
    left_evidence_id: UUID
    right_evidence_id: UUID
    correlation_id: str
    correlation_type: CorrelationType
    score: float
    confidence: float
    explanation: str
    supporting_findings: list[str] = Field(default_factory=list)
    supporting_metadata: dict[str, Any] = Field(default_factory=dict)
    supporting_entities: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    supports: list[CorrelationSupportResponse] = Field(default_factory=list)
    created_at: datetime


class CorrelationRunResponse(BaseModel):
    """Summary of one correlation analysis run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    status: CorrelationRunStatus
    engine_version: str
    policy_version: str
    correlation_count: int
    evidence_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)


class CorrelationDetailResponse(CorrelationRunResponse):
    """Correlation run with relationship list."""

    correlations: list[EvidenceCorrelationResponse] = Field(default_factory=list)


class CorrelationRunListResponse(BaseModel):
    """Paginated correlation history for one case."""

    items: list[CorrelationRunResponse]
    total: int
    limit: int
    offset: int
