"""SQLAlchemy persistence models for AI image forensic analysis."""

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

from backend.app.ai.image.models import ImageAnalysisRunStatus, ImageFindingCategory
from backend.app.forensics.models import Severity
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence
    from backend.app.models.processing import Artifact


class ImageAnalysisRun(Base):
    """One AI image forensic analysis execution."""

    __tablename__ = "image_analysis_runs"
    __table_args__ = (Index("ix_image_analysis_runs_evidence_id", "evidence_id"),)

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
    status: Mapped[ImageAnalysisRunStatus] = mapped_column(
        Enum(ImageAnalysisRunStatus, native_enum=False, length=16),
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

    evidence: Mapped["Evidence"] = relationship(back_populates="image_analysis_runs")
    findings: Mapped[list["ImageAIFinding"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ImageAIFinding.created_at",
    )


class ImageAIFinding(Base):
    """One persisted AI image forensic finding."""

    __tablename__ = "image_ai_findings"
    __table_args__ = (
        Index("ix_image_ai_findings_analysis_run_id", "analysis_run_id"),
        Index("ix_image_ai_findings_evidence_id", "evidence_id"),
        Index("ix_image_ai_findings_detector", "detector"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("image_analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    detector: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[ImageFindingCategory] = mapped_column(
        Enum(ImageFindingCategory, native_enum=False, length=32),
        nullable=False,
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False, length=16),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model_framework: Mapped[str] = mapped_column(String(32), nullable=False)
    heatmap_artifact_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    mask_artifact_id: Mapped[UUID | None] = mapped_column(
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

    analysis_run: Mapped["ImageAnalysisRun"] = relationship(back_populates="findings")
    evidence: Mapped["Evidence"] = relationship(back_populates="image_ai_findings")
    heatmap_artifact: Mapped["Artifact | None"] = relationship(
        foreign_keys=[heatmap_artifact_id],
    )
    mask_artifact: Mapped["Artifact | None"] = relationship(
        foreign_keys=[mask_artifact_id],
    )
    regions: Mapped[list["ImageAIFindingRegion"]] = relationship(
        back_populates="finding",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ImageAIFindingRegion.created_at",
    )


class ImageAIFindingRegion(Base):
    """Localized region attached to one AI image finding."""

    __tablename__ = "image_ai_finding_regions"
    __table_args__ = (Index("ix_image_ai_finding_regions_finding_id", "finding_id"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    finding_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("image_ai_findings.id", ondelete="CASCADE"),
        nullable=False,
    )
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    page_number: Mapped[int | None] = mapped_column(nullable=True)
    frame_number: Mapped[int | None] = mapped_column(nullable=True)
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

    finding: Mapped["ImageAIFinding"] = relationship(back_populates="regions")
