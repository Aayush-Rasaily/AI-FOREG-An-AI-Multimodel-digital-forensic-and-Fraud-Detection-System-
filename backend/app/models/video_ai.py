"""SQLAlchemy persistence models for AI video forensic analysis."""

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

from backend.app.ai.video.models.base import (
    DetectionMethod,
    VideoAnalysisRunStatus,
    VideoFindingCategory,
)
from backend.app.forensics.models import Severity
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence
    from backend.app.models.processing import Artifact


class VideoAnalysisRun(Base):
    """One video AI forensic analysis execution."""

    __tablename__ = "video_analysis_runs"
    __table_args__ = (Index("ix_video_analysis_runs_evidence_id", "evidence_id"),)

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
    status: Mapped[VideoAnalysisRunStatus] = mapped_column(
        Enum(VideoAnalysisRunStatus, native_enum=False, length=16),
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

    evidence: Mapped["Evidence"] = relationship(back_populates="video_analysis_runs")
    findings: Mapped[list["VideoAIFinding"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="VideoAIFinding.created_at",
    )


class VideoAIFinding(Base):
    """One persisted video AI forensic finding."""

    __tablename__ = "video_ai_findings"
    __table_args__ = (
        Index("ix_video_ai_findings_analysis_run_id", "analysis_run_id"),
        Index("ix_video_ai_findings_evidence_id", "evidence_id"),
        Index("ix_video_ai_findings_detector", "detector"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("video_analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    detector: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[VideoFindingCategory] = mapped_column(
        Enum(VideoFindingCategory, native_enum=False, length=32),
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
    start_frame: Mapped[int | None] = mapped_column(nullable=True)
    end_frame: Mapped[int | None] = mapped_column(nullable=True)
    start_timestamp_ms: Mapped[int | None] = mapped_column(nullable=True)
    end_timestamp_ms: Mapped[int | None] = mapped_column(nullable=True)
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

    analysis_run: Mapped["VideoAnalysisRun"] = relationship(back_populates="findings")
    evidence: Mapped["Evidence"] = relationship(back_populates="video_ai_findings")
    artifact: Mapped["Artifact | None"] = relationship(
        foreign_keys=[artifact_id],
    )
    regions: Mapped[list["VideoAIFindingRegion"]] = relationship(
        back_populates="finding",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="VideoAIFindingRegion.created_at",
    )


class VideoAIFindingRegion(Base):
    """Localized region attached to one video AI finding."""

    __tablename__ = "video_ai_finding_regions"
    __table_args__ = (Index("ix_video_ai_finding_regions_finding_id", "finding_id"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    finding_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("video_ai_findings.id", ondelete="CASCADE"),
        nullable=False,
    )
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    frame_number: Mapped[int | None] = mapped_column(nullable=True)
    timestamp_ms: Mapped[int | None] = mapped_column(nullable=True)
    polygon_json: Mapped[list[list[float]] | None] = mapped_column(
        "polygon",
        JSON,
        nullable=True,
    )
    normalized_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_width: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    finding: Mapped["VideoAIFinding"] = relationship(back_populates="regions")
