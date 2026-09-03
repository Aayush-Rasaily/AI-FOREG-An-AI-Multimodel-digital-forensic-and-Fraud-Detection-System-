"""API schemas for forensic investigation reports."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.reporting.models import ReportStatus


class ForensicReportResponse(BaseModel):
    id: UUID
    case_id: UUID
    status: ReportStatus
    report_version: str
    engine_version: str
    fusion_policy_version: str | None
    case_intelligence_policy_version: str | None
    case_intelligence_run_id: UUID | None
    evidence_count: int
    evidence_hashes: list[str]
    pdf_sha256: str | None
    has_pdf: bool
    report_checksum: str | None = None
    included_analysis_run_ids: dict[str, Any] = Field(
        default_factory=dict,
    )
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any]
    provenance: dict[str, Any]


class ForensicReportListResponse(BaseModel):
    items: list[ForensicReportResponse]
    total: int
    limit: int
    offset: int


class ForensicReportDetailResponse(ForensicReportResponse):
    content: dict[str, Any] = Field(default_factory=dict)
    executive_summary: dict[str, Any] = Field(default_factory=dict)
    explainability: dict[str, Any] = Field(default_factory=dict)
    section_order: list[str] = Field(default_factory=list)


class ForensicReportStatusResponse(BaseModel):
    id: UUID
    status: ReportStatus
    error_code: str | None
    error_message: str | None
    completed_at: datetime | None
