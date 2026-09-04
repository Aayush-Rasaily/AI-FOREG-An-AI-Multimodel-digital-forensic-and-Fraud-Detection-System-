"""API schemas for interoperability endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    format: str = Field(description="Export format identifier.")
    evidence_ids: list[UUID] | None = Field(
        default=None,
        description="Optional selective evidence export.",
    )
    include_binaries: bool = False


class ExportJobResponse(BaseModel):
    id: UUID
    case_id: UUID
    format: str
    status: str
    package_version: str
    schema_version: str
    storage_key: str | None = None
    package_checksum: str | None = None
    manifest_checksum: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    report_versions: list[str] = Field(default_factory=list)
    timeline_version: str | None = None
    policy_versions: dict[str, str] = Field(default_factory=dict)
    error_message: str | None = None
    created_by: str | None = None
    engine_version: str
    policy_version: str
    created_at: datetime
    completed_at: datetime | None = None


class ExportJobListResponse(BaseModel):
    items: list[ExportJobResponse]
    total: int


class ImportJobResponse(BaseModel):
    id: UUID
    source_filename: str | None = None
    status: str
    package_version: str | None = None
    schema_version: str | None = None
    integrity_status: str
    validation: dict[str, Any] = Field(default_factory=dict)
    conflicts: list[str] = Field(default_factory=list)
    package_checksum: str | None = None
    storage_key: str | None = None
    target_case_id: UUID | None = None
    error_message: str | None = None
    created_by: str | None = None
    engine_version: str
    policy_version: str
    created_at: datetime
    completed_at: datetime | None = None


class ImportJobListResponse(BaseModel):
    items: list[ImportJobResponse]
    total: int


class ManifestResponse(BaseModel):
    export_job_id: UUID
    manifest: dict[str, Any]
    manifest_checksum: str
    package_checksum: str
