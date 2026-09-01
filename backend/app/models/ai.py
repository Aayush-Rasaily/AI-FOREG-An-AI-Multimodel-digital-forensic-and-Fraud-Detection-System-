"""SQLAlchemy persistence models for AI infrastructure."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.infrastructure.database.base import Base


class AIModelStatus(StrEnum):
    """Lifecycle status for a registered model record."""

    REGISTERED = "REGISTERED"
    LOADED = "LOADED"
    UNLOADED = "UNLOADED"
    FAILED = "FAILED"


class InferenceJobStatus(StrEnum):
    """Inference job lifecycle."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class AIModelRecord(Base):
    """Persisted metadata for one registered AI model."""

    __tablename__ = "ai_model_records"
    __table_args__ = (Index("ix_ai_model_records_name", "name"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    framework: Mapped[str] = mapped_column(String(32), nullable=False)
    author: Mapped[str] = mapped_column(String(128), nullable=False)
    license: Mapped[str] = mapped_column(String(64), nullable=False)
    input_type: Mapped[str] = mapped_column(String(32), nullable=False)
    output_type: Mapped[str] = mapped_column(String(32), nullable=False)
    model_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    required_device: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[AIModelStatus] = mapped_column(
        Enum(AIModelStatus, native_enum=False, length=16),
        nullable=False,
        default=AIModelStatus.REGISTERED,
    )
    current_device: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_loaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    inference_jobs: Mapped[list["InferenceJob"]] = relationship(
        back_populates="model_record",
        passive_deletes=True,
    )


class InferenceJob(Base):
    """One inference execution tracked by the platform."""

    __tablename__ = "inference_jobs"
    __table_args__ = (
        Index("ix_inference_jobs_model_record_id", "model_record_id"),
        Index("ix_inference_jobs_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    model_record_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_model_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    task: Mapped[str] = mapped_column(String(64), nullable=False)
    device: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[InferenceJobStatus] = mapped_column(
        Enum(InferenceJobStatus, native_enum=False, length=16),
        nullable=False,
    )
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    batch_size: Mapped[int] = mapped_column(nullable=False, default=1)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    model_record: Mapped["AIModelRecord"] = relationship(
        back_populates="inference_jobs"
    )
    logs: Mapped[list["InferenceLog"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class InferenceLog(Base):
    """Structured log entry for one inference job."""

    __tablename__ = "inference_logs"
    __table_args__ = (Index("ix_inference_logs_job_id", "job_id"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("inference_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    job: Mapped["InferenceJob"] = relationship(back_populates="logs")
