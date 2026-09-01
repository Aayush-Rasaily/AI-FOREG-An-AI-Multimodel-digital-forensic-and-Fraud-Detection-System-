"""SQLAlchemy persistence for case-level forensic intelligence."""

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
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.case_intelligence.models import (
    CaseConflictType,
    CaseIntelligenceRunStatus,
    ConflictResolutionStatus,
    RelationshipStatus,
    RelationshipType,
    TimelineEventType,
)
from backend.app.forensics.models import Severity
from backend.app.fusion.models import FusionVerdict
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.case import Case


class CaseIntelligenceRun(Base):
    """One case-level forensic intelligence synthesis execution."""

    __tablename__ = "case_intelligence_runs"
    __table_args__ = (
        Index("ix_case_intelligence_runs_case_id", "case_id"),
        Index(
            "uq_case_intelligence_runs_active",
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
    status: Mapped[CaseIntelligenceRunStatus] = mapped_column(
        Enum(CaseIntelligenceRunStatus, native_enum=False, length=16),
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
    evidence_count: Mapped[int] = mapped_column(nullable=False, default=0)
    conflicts_count: Mapped[int] = mapped_column(nullable=False, default=0)
    relationships_count: Mapped[int] = mapped_column(nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    coverage_json: Mapped[dict[str, Any]] = mapped_column(
        "coverage",
        JSON,
        nullable=False,
        default=dict,
    )
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

    case: Mapped["Case"] = relationship(back_populates="case_intelligence_runs")
    participations: Mapped[list["CaseEvidenceParticipationRecord"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CaseEvidenceParticipationRecord.created_at",
    )
    relationships: Mapped[list["CaseRelationshipRecord"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CaseRelationshipRecord.created_at",
    )
    conflicts: Mapped[list["CaseConflictRecord"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CaseConflictRecord.created_at",
    )
    timeline_events: Mapped[list["CaseTimelineEventRecord"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CaseTimelineEventRecord.created_at",
    )


class CaseEvidenceParticipationRecord(Base):
    """Persisted evidence participation in one case intelligence run."""

    __tablename__ = "case_evidence_participation_records"
    __table_args__ = (
        Index(
            "ix_case_evidence_participation_records_analysis_run_id",
            "analysis_run_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    evidence_number: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_status: Mapped[str] = mapped_column(String(32), nullable=False)
    coverage_status: Mapped[str] = mapped_column(String(32), nullable=False)
    fusion_run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )
    fusion_verdict: Mapped[FusionVerdict | None] = mapped_column(
        Enum(FusionVerdict, native_enum=False, length=32),
        nullable=True,
    )
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
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
    conflicts_count: Mapped[int] = mapped_column(nullable=False, default=0)
    participating_modalities: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    unavailable_modalities: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    fusion_engine_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fusion_policy_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fusion_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    analysis_run: Mapped["CaseIntelligenceRun"] = relationship(
        back_populates="participations"
    )


class CaseRelationshipRecord(Base):
    """Persisted cross-evidence relationship."""

    __tablename__ = "case_relationship_records"
    __table_args__ = (
        Index("ix_case_relationship_records_analysis_run_id", "analysis_run_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_id: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_a_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    evidence_b_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, native_enum=False, length=32),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    supporting_reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_reference: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[RelationshipStatus] = mapped_column(
        Enum(RelationshipStatus, native_enum=False, length=16),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    analysis_run: Mapped["CaseIntelligenceRun"] = relationship(
        back_populates="relationships"
    )


class CaseConflictRecord(Base):
    """Persisted case-level conflict."""

    __tablename__ = "case_conflict_records"
    __table_args__ = (
        Index("ix_case_conflict_records_analysis_run_id", "analysis_run_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    conflict_id: Mapped[str] = mapped_column(String(128), nullable=False)
    conflict_type: Mapped[CaseConflictType] = mapped_column(
        Enum(CaseConflictType, native_enum=False, length=32),
        nullable=False,
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False, length=16),
        nullable=False,
    )
    involved_evidence_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    involved_finding_ids: Mapped[list[str]] = mapped_column(
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

    analysis_run: Mapped["CaseIntelligenceRun"] = relationship(
        back_populates="conflicts"
    )


class CaseTimelineEventRecord(Base):
    """Persisted case timeline event."""

    __tablename__ = "case_timeline_event_records"
    __table_args__ = (
        Index("ix_case_timeline_event_records_analysis_run_id", "analysis_run_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[TimelineEventType] = mapped_column(
        Enum(TimelineEventType, native_enum=False, length=32),
        nullable=False,
    )
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    timestamp_known: Mapped[bool] = mapped_column(nullable=False, default=False)
    evidence_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    source_reference: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
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

    analysis_run: Mapped["CaseIntelligenceRun"] = relationship(
        back_populates="timeline_events"
    )
