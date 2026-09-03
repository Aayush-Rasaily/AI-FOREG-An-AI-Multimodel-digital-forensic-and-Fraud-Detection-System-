"""SQLAlchemy persistence for cross-evidence correlation."""

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
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.correlation.models import CorrelationRunStatus, CorrelationType
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.case import Case


class CorrelationAnalysisRun(Base):
    """One persisted cross-evidence correlation analysis run."""

    __tablename__ = "correlation_analysis_runs"
    __table_args__ = (
        Index("ix_correlation_analysis_runs_case_id", "case_id"),
        Index(
            "uq_correlation_analysis_runs_active",
            "case_id",
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
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[CorrelationRunStatus] = mapped_column(
        Enum(CorrelationRunStatus, native_enum=False, length=16),
        nullable=False,
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    correlation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance",
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

    case: Mapped["Case"] = relationship(back_populates="correlation_analysis_runs")
    correlations: Mapped[list["EvidenceCorrelationRecord"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
    )


class EvidenceCorrelationRecord(Base):
    """One deterministic relationship between two evidence items."""

    __tablename__ = "evidence_correlations"
    __table_args__ = (
        Index("ix_evidence_correlations_analysis_run_id", "analysis_run_id"),
        Index("ix_evidence_correlations_case_id", "case_id"),
        Index("ix_evidence_correlations_left_evidence_id", "left_evidence_id"),
        Index("ix_evidence_correlations_right_evidence_id", "right_evidence_id"),
        Index(
            "uq_evidence_correlations_pair_type",
            "analysis_run_id",
            "left_evidence_id",
            "right_evidence_id",
            "correlation_type",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("correlation_analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    left_evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    right_evidence_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    correlation_id: Mapped[str] = mapped_column(String(256), nullable=False)
    correlation_type: Mapped[CorrelationType] = mapped_column(
        Enum(CorrelationType, native_enum=False, length=64),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_findings_json: Mapped[list[str]] = mapped_column(
        "supporting_findings",
        JSON,
        nullable=False,
        default=list,
    )
    supporting_metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "supporting_metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    supporting_entities_json: Mapped[list[str]] = mapped_column(
        "supporting_entities",
        JSON,
        nullable=False,
        default=list,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance",
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

    analysis_run: Mapped[CorrelationAnalysisRun] = relationship(
        back_populates="correlations"
    )
    support_records: Mapped[list["CorrelationSupportRecord"]] = relationship(
        back_populates="correlation",
        cascade="all, delete-orphan",
    )


class CorrelationSupportRecord(Base):
    """Supporting artifact/finding for one correlation."""

    __tablename__ = "correlation_support_records"
    __table_args__ = (
        Index("ix_correlation_support_records_correlation_id", "correlation_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    correlation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence_correlations.id", ondelete="CASCADE"),
        nullable=False,
    )
    support_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    support_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    correlation: Mapped[EvidenceCorrelationRecord] = relationship(
        back_populates="support_records"
    )
