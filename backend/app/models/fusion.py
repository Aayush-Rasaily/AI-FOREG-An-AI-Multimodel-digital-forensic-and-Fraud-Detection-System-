"""SQLAlchemy persistence for multimodal fusion."""

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

from backend.app.forensics.models import Severity
from backend.app.fusion.models import (
    ConflictResolutionStatus,
    ConflictType,
    FusionRunStatus,
    FusionVerdict,
    JuryMemberRole,
    ModalityAvailability,
)
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence


class FusionAnalysisRun(Base):
    """One multimodal fusion analysis execution."""

    __tablename__ = "fusion_analysis_runs"
    __table_args__ = (Index("ix_fusion_analysis_runs_evidence_id", "evidence_id"),)

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
    status: Mapped[FusionRunStatus] = mapped_column(
        Enum(FusionRunStatus, native_enum=False, length=16),
        nullable=False,
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    verdict: Mapped[FusionVerdict | None] = mapped_column(
        Enum(FusionVerdict, native_enum=False, length=32),
        nullable=True,
    )
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    findings_count: Mapped[int] = mapped_column(nullable=False, default=0)
    conflicts_count: Mapped[int] = mapped_column(nullable=False, default=0)
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
    modality_status_json: Mapped[list[dict[str, Any]]] = mapped_column(
        "modality_status",
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

    evidence: Mapped["Evidence"] = relationship(back_populates="fusion_analysis_runs")
    jury_assessments: Mapped[list["JuryAssessmentRecord"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="JuryAssessmentRecord.created_at",
    )
    conflicts: Mapped[list["FusionConflictRecord"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="FusionConflictRecord.created_at",
    )


class JuryAssessmentRecord(Base):
    """Persisted jury member assessment."""

    __tablename__ = "jury_assessment_records"
    __table_args__ = (
        Index("ix_jury_assessment_records_analysis_run_id", "analysis_run_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("fusion_analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[JuryMemberRole] = mapped_column(
        Enum(JuryMemberRole, native_enum=False, length=32),
        nullable=False,
    )
    member_name: Mapped[str] = mapped_column(String(128), nullable=False)
    verdict: Mapped[FusionVerdict] = mapped_column(
        Enum(FusionVerdict, native_enum=False, length=32),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    availability: Mapped[ModalityAvailability] = mapped_column(
        Enum(ModalityAvailability, native_enum=False, length=24),
        nullable=False,
    )
    supporting_finding_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    contradictory_finding_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    model_version: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    analysis_run: Mapped["FusionAnalysisRun"] = relationship(
        back_populates="jury_assessments"
    )


class FusionConflictRecord(Base):
    """Persisted cross-modal conflict."""

    __tablename__ = "fusion_conflict_records"
    __table_args__ = (
        Index("ix_fusion_conflict_records_analysis_run_id", "analysis_run_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("fusion_analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    conflict_id: Mapped[str] = mapped_column(String(128), nullable=False)
    conflict_type: Mapped[ConflictType] = mapped_column(
        Enum(ConflictType, native_enum=False, length=32),
        nullable=False,
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False, length=16),
        nullable=False,
    )
    involved_finding_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    involved_modalities: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_status: Mapped[ConflictResolutionStatus] = mapped_column(
        Enum(ConflictResolutionStatus, native_enum=False, length=16),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    analysis_run: Mapped["FusionAnalysisRun"] = relationship(back_populates="conflicts")
