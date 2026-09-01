"""SQLAlchemy persistence models for reference comparison."""

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

from backend.app.comparison.models import (
    ComparisonRunStatus,
    DifferenceSeverity,
    DifferenceType,
)
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.case import Case
    from backend.app.models.evidence import Evidence


class ReferenceEvidence(Base):
    """Immutable trusted reference linked to one case."""

    __tablename__ = "reference_evidence"
    __table_args__ = (
        Index("ix_reference_evidence_case_id", "case_id"),
        Index("ix_reference_evidence_evidence_id", "evidence_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_hash: Mapped[str] = mapped_column(String(64), nullable=False)
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

    case: Mapped["Case"] = relationship(back_populates="reference_evidence")
    evidence: Mapped["Evidence"] = relationship(
        back_populates="reference_records",
        foreign_keys=[evidence_id],
    )
    comparison_runs: Mapped[list["ComparisonRun"]] = relationship(
        back_populates="reference_record",
        passive_deletes=True,
    )


class ComparisonRun(Base):
    """One reference comparison execution."""

    __tablename__ = "comparison_runs"
    __table_args__ = (
        Index("ix_comparison_runs_evidence_id", "evidence_id"),
        Index("ix_comparison_runs_reference_record_id", "reference_record_id"),
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
    reference_record_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reference_evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    reference_evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    processing_job_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processing_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[ComparisonRunStatus] = mapped_column(
        Enum(ComparisonRunStatus, native_enum=False, length=16),
        nullable=False,
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    differences_count: Mapped[int] = mapped_column(nullable=False, default=0)
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

    evidence: Mapped["Evidence"] = relationship(
        back_populates="comparison_runs",
        foreign_keys=[evidence_id],
    )
    reference_record: Mapped["ReferenceEvidence"] = relationship(
        back_populates="comparison_runs",
    )
    differences: Mapped[list["Difference"]] = relationship(
        back_populates="comparison_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Difference.created_at",
    )


class Difference(Base):
    """One persisted comparison difference."""

    __tablename__ = "differences"
    __table_args__ = (
        Index("ix_differences_comparison_run_id", "comparison_run_id"),
        Index("ix_differences_evidence_id", "evidence_id"),
        Index("ix_differences_matcher", "matcher"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    comparison_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("comparison_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    matcher: Mapped[str] = mapped_column(String(64), nullable=False)
    difference_type: Mapped[DifferenceType] = mapped_column(
        Enum(DifferenceType, native_enum=False, length=32),
        nullable=False,
    )
    severity: Mapped[DifferenceSeverity] = mapped_column(
        Enum(DifferenceSeverity, native_enum=False, length=16),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    original_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_value: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    comparison_run: Mapped["ComparisonRun"] = relationship(back_populates="differences")
    evidence: Mapped["Evidence"] = relationship(back_populates="differences")
    regions: Mapped[list["DifferenceRegion"]] = relationship(
        back_populates="difference",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DifferenceRegion.created_at",
    )


class DifferenceRegion(Base):
    """Localized region attached to one comparison difference."""

    __tablename__ = "difference_regions"
    __table_args__ = (Index("ix_difference_regions_difference_id", "difference_id"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    difference_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("differences.id", ondelete="CASCADE"),
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

    difference: Mapped["Difference"] = relationship(back_populates="regions")
