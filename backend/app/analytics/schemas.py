"""API schemas for Phase 9G analytics."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MetricResponse(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    category: str
    provenance: dict[str, Any] = Field(default_factory=dict)


class AnalyticsRunResponse(BaseModel):
    id: UUID | None = None
    status: str
    metric_count: int
    metrics: list[MetricResponse] = Field(default_factory=list)
    sections: dict[str, Any] = Field(default_factory=dict)
    trends: dict[str, Any] = Field(default_factory=dict)
    dashboard: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    engine_version: str
    policy_version: str
    created_at: datetime | None = None
    completed_at: datetime | None = None
    persisted: bool = True


class AnalyticsSectionResponse(BaseModel):
    section: str
    data: dict[str, Any]
    engine_version: str
    policy_version: str
    generated_at: datetime | None = None


class AnalyticsExportResponse(BaseModel):
    format: str = "json"
    generated_at: datetime
    engine_version: str
    policy_version: str
    payload: dict[str, Any]
