"""SQLAlchemy persistence models for processing jobs and artifacts."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.domain.processing import (
    ArtifactType,
    ProcessingJobStatus,
    ProcessingJobType,
)
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence
    from backend.app.models.extraction import ExtractionRecord


class ProcessingJob(Base):
    """One asynchronous-ready processing pipeline execution for evidence."""

    __tablename__ = "processing_jobs"
    __table_args__ = (
        Index("ix_processing_jobs_evidence_id", "evidence_id"),
        Index("ix_processing_jobs_status", "status"),
        Index("ix_processing_jobs_created_at", "created_at"),
        Index(
            "uq_processing_jobs_active",
            "evidence_id",
            "job_type",
            unique=True,
            postgresql_where=text("status IN ('QUEUED', 'RUNNING')"),
            sqlite_where=text("status IN ('QUEUED', 'RUNNING')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_type: Mapped[ProcessingJobType] = mapped_column(
        Enum(ProcessingJobType, native_enum=False, length=64),
        nullable=False,
    )
    status: Mapped[ProcessingJobStatus] = mapped_column(
        Enum(ProcessingJobStatus, native_enum=False, length=16),
        nullable=False,
        default=ProcessingJobStatus.QUEUED,
    )
    priority: Mapped[int] = mapped_column(nullable=False, default=0)
    attempt: Mapped[int] = mapped_column(nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message_safe: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

    evidence: Mapped["Evidence"] = relationship(
        back_populates="processing_jobs",
    )


class Artifact(Base):
    """A separately stored, independently hashed derivative of evidence."""

    __tablename__ = "artifacts"
    __table_args__ = (
        Index("ix_artifacts_evidence_id", "evidence_id"),
        Index("ix_artifacts_artifact_type", "artifact_type"),
        Index("ix_artifacts_created_at", "created_at"),
        Index("ix_artifacts_sha256_hash", "sha256_hash"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, native_enum=False, length=32),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

    evidence: Mapped["Evidence"] = relationship(
        back_populates="artifacts",
    )
    extraction_records: Mapped[list["ExtractionRecord"]] = relationship(
        back_populates="artifact",
    )
