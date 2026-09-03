"""API schemas for system administration."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class HealthSnapshotResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    version: str
    environment: str
    uptime_seconds: float
    python_version: str
    platform: str
    database: dict[str, Any]
    redis: dict[str, Any]
    resources: dict[str, Any]
    engine_version: str
    policy_version: str


class MetricsResponse(BaseModel):
    evidence_count: int
    case_count: int
    report_count: int
    timeline_count: int
    fusion_run_count: int
    entity_graph_count: int
    correlation_count: int
    ai_analysis_count: int
    processing_job_count: int
    average_processing_time_ms: float | None
    failure_rate: float
    storage_growth_bytes: int | None


class JobsSummaryResponse(BaseModel):
    categories: dict[str, dict[str, int]]
    totals: dict[str, int]
    active_analyses: int
    queue_length: int
    category_list: list[str]


class StorageStatsResponse(BaseModel):
    backend: str
    root_configured: bool
    used_bytes: int
    used_mb: float
    disk_total_bytes: int | None
    disk_free_bytes: int | None
    disk_percent: float | None
    max_upload_size_mb: int


class DiagnosticCheckResponse(BaseModel):
    name: str
    status: str
    detail: str


class DiagnosticsResponse(BaseModel):
    overall_status: str
    checks: list[DiagnosticCheckResponse]
    check_names: list[str]
    pass_count: int
    warn_count: int
    fail_count: int


class DiagnosticsRunResponse(BaseModel):
    id: UUID
    overall_status: str
    results_json: dict[str, Any]
    engine_version: str
    policy_version: str
    created_at: datetime
