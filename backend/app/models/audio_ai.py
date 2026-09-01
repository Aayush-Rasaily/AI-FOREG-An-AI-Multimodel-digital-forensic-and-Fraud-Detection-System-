"""SQLAlchemy persistence models for AI audio forensic analysis."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
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

from backend.app.ai.audio.models import (
    AudioAnalysisRunStatus,
    AudioFindingCategory,
    DetectionMethod,
)
from backend.app.forensics.models import Severity
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence
    from backend.app.models.processing import Artifact


class AudioAnalysisRun(Base):
    """One audio AI forensic analysis execution."""

    __tablename__ = "audio_analysis_runs"
    __table_args__ = (Index("ix_audio_analysis_runs_evidence_id", "evidence_id"),)

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
    processing_job_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processing_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    reference_evidence_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[AudioAnalysisRunStatus] = mapped_column(
        Enum(AudioAnalysisRunStatus, native_enum=False, length=16),
        nullable=False,
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    device: Mapped[str] = mapped_column(String(16), nullable=False, default="cpu")
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    findings_count: Mapped[int] = mapped_column(nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    timeline_json: Mapped[list[dict[str, Any]]] = mapped_column(
        "timeline",
        JSON,
        nullable=False,
        default=list,
    )
    segments_json: Mapped[list[dict[str, Any]]] = mapped_column(
        "segments",
        JSON,
        nullable=False,
        default=list,
    )
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

    evidence: Mapped["Evidence"] = relationship(
        back_populates="audio_analysis_runs",
        foreign_keys=[evidence_id],
    )
    findings: Mapped[list["AudioAIFinding"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AudioAIFinding.created_at",
    )


class AudioAIFinding(Base):
    """One persisted audio AI forensic finding."""

    __tablename__ = "audio_ai_findings"
    __table_args__ = (
        Index("ix_audio_ai_findings_analysis_run_id", "analysis_run_id"),
        Index("ix_audio_ai_findings_evidence_id", "evidence_id"),
        Index("ix_audio_ai_findings_detector", "detector"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audio_analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    detector: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[AudioFindingCategory] = mapped_column(
        Enum(AudioFindingCategory, native_enum=False, length=32),
        nullable=False,
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False, length=16),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    method: Mapped[DetectionMethod] = mapped_column(
        Enum(DetectionMethod, native_enum=False, length=16),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model_framework: Mapped[str] = mapped_column(String(32), nullable=False)
    start_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    end_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    artifact_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
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

    analysis_run: Mapped["AudioAnalysisRun"] = relationship(back_populates="findings")
    evidence: Mapped["Evidence"] = relationship(back_populates="audio_ai_findings")
    artifact: Mapped["Artifact | None"] = relationship(
        foreign_keys=[artifact_id],
    )
    regions: Mapped[list["AudioAIFindingRegion"]] = relationship(
        back_populates="finding",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AudioAIFindingRegion.created_at",
    )


class AudioAIFindingRegion(Base):
    """Localized temporal region attached to one audio AI finding."""

    __tablename__ = "audio_ai_finding_regions"
    __table_args__ = (Index("ix_audio_ai_finding_regions_finding_id", "finding_id"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    finding_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audio_ai_findings.id", ondelete="CASCADE"),
        nullable=False,
    )
    segment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    start_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    end_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    metrics_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metrics",
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    finding: Mapped["AudioAIFinding"] = relationship(back_populates="regions")
