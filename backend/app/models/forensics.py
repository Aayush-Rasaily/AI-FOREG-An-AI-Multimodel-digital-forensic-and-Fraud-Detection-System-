"""SQLAlchemy persistence models for forensic analysis runs and findings."""

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

from backend.app.forensics.models import (
    AnalysisRunStatus,
    FindingCategory,
    Severity,
)
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence


class AnalysisRun(Base):
    """One deterministic forensic analysis execution for an evidence item."""

    __tablename__ = "analysis_runs"
    __table_args__ = (Index("ix_analysis_runs_evidence_id", "evidence_id"),)

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
    status: Mapped[AnalysisRunStatus] = mapped_column(
        Enum(AnalysisRunStatus, native_enum=False, length=16),
        nullable=False,
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
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

    evidence: Mapped["Evidence"] = relationship(back_populates="analysis_runs")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Finding.created_at",
    )


class Finding(Base):
    """One persisted forensic finding from a detector."""

    __tablename__ = "findings"
    __table_args__ = (
        Index("ix_findings_analysis_run_id", "analysis_run_id"),
        Index("ix_findings_evidence_id", "evidence_id"),
        Index("ix_findings_detector", "detector"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    detector: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[FindingCategory] = mapped_column(
        Enum(FindingCategory, native_enum=False, length=32),
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

    analysis_run: Mapped["AnalysisRun"] = relationship(back_populates="findings")
    evidence: Mapped["Evidence"] = relationship(back_populates="findings")
    regions: Mapped[list["FindingRegion"]] = relationship(
        back_populates="finding",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="FindingRegion.created_at",
    )


class FindingRegion(Base):
    """Localized region attached to one forensic finding."""

    __tablename__ = "finding_regions"
    __table_args__ = (Index("ix_finding_regions_finding_id", "finding_id"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    finding_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
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

    finding: Mapped["Finding"] = relationship(back_populates="regions")
