"""Pydantic contracts for processing jobs and derived artifacts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.domain.processing import (
    ArtifactType,
    ProcessingJobStatus,
    ProcessingJobType,
)


class ProcessingJobResponse(BaseModel):
    """Public processing job state without internal exception details."""

    id: UUID
    evidence_id: UUID
    job_type: ProcessingJobType
    status: ProcessingJobStatus
    priority: int
    attempt: int
    max_attempts: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime
    error_code: str | None
    error_message: str | None = Field(
        default=None,
        description="Safe operator-facing processing message.",
    )
    metadata: dict[str, object]


class ProcessingJobListResponse(BaseModel):
    """Paginated processing job collection."""

    items: list[ProcessingJobResponse]
    total: int
    limit: int
    offset: int


class ArtifactResponse(BaseModel):
    """Public metadata for one independently stored derivative."""

    id: UUID
    evidence_id: UUID
    artifact_type: ArtifactType
    mime_type: str
    file_size: int
    sha256_hash: str
    created_at: datetime
    metadata: dict[str, object]


class ArtifactListResponse(BaseModel):
    """Paginated artifact collection for one evidence item."""

    items: list[ArtifactResponse]
    total: int
    limit: int
    offset: int
