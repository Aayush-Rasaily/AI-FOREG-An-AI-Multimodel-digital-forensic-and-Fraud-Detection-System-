"""Pydantic schemas for operational monitoring responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MonitoringDashboardResponse(BaseModel):
    """Full operational dashboard payload."""

    model_config = ConfigDict(extra="forbid")

    system_health: dict[str, Any]
    processing: dict[str, Any]
    ai: dict[str, Any]
    cases: dict[str, Any]
    reports: dict[str, Any]
    api: dict[str, Any]
    activity: dict[str, Any]
    bottlenecks: dict[str, Any]
    audit_summary: dict[str, Any]
    kpis: dict[str, Any]
    trends: dict[str, Any]
    recent_failures: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: str
    engine_version: str
    policy_version: str
    snapshot_id: UUID | None = None


class SystemHealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    reasons: list[str]
    signals: dict[str, Any]
    assessed_at: str
    engine_version: str
    policy_version: str


class MonitoringSectionResponse(BaseModel):
    """Generic section wrapper for domain metrics."""

    model_config = ConfigDict(extra="forbid")

    data: dict[str, Any]
    generated_at: str
    engine_version: str
    policy_version: str


class MonitoringRefreshResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: UUID
    health_record_id: UUID
    audit_statistics_id: UUID
    generated_at: datetime
    system_health: dict[str, Any]
    engine_version: str
    policy_version: str
