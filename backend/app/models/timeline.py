"""SQLAlchemy persistence for investigation timelines."""

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

from backend.app.infrastructure.database.base import Base
from backend.app.timeline.models import (
    TimelineConflictType,
    TimelineEventType,
    TimelineRunStatus,
)

if TYPE_CHECKING:
    from backend.app.models.case import Case


class InvestigationTimeline(Base):
    """One persisted investigation timeline reconstruction run."""

    __tablename__ = "investigation_timelines"
    __table_args__ = (
        Index("ix_investigation_timelines_case_id", "case_id"),
        Index(
            "uq_investigation_timelines_active",
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
    status: Mapped[TimelineRunStatus] = mapped_column(
        Enum(TimelineRunStatus, native_enum=False, length=16),
        nullable=False,
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflicts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    case: Mapped["Case"] = relationship(back_populates="investigation_timelines")
    events: Mapped[list["TimelineEventRecord"]] = relationship(
        back_populates="timeline",
        cascade="all, delete-orphan",
    )
    conflicts: Mapped[list["TimelineConflictRecord"]] = relationship(
        back_populates="timeline",
        cascade="all, delete-orphan",
    )


class TimelineEventRecord(Base):
    """One chronological event within an investigation timeline."""

    __tablename__ = "timeline_events"
    __table_args__ = (
        Index("ix_timeline_events_timeline_id", "timeline_id"),
        Index("ix_timeline_events_case_id", "case_id"),
        Index("ix_timeline_events_evidence_id", "evidence_id"),
        Index("ix_timeline_events_event_id", "timeline_id", "event_id", unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    timeline_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigation_timelines.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[TimelineEventType] = mapped_column(
        Enum(TimelineEventType, native_enum=False, length=64),
        nullable=False,
    )
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    normalized_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    uncertainty_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance",
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
    supporting_artifacts_json: Mapped[list[str]] = mapped_column(
        "supporting_artifacts",
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

    timeline: Mapped[InvestigationTimeline] = relationship(back_populates="events")


class TimelineConflictRecord(Base):
    """One detected timestamp conflict within an investigation timeline."""

    __tablename__ = "timeline_conflicts"
    __table_args__ = (
        Index("ix_timeline_conflicts_timeline_id", "timeline_id"),
        Index("ix_timeline_conflicts_case_id", "case_id"),
        Index(
            "ix_timeline_conflicts_conflict_id",
            "timeline_id",
            "conflict_id",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    timeline_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigation_timelines.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    conflict_id: Mapped[str] = mapped_column(String(128), nullable=False)
    conflict_type: Mapped[TimelineConflictType] = mapped_column(
        Enum(TimelineConflictType, native_enum=False, length=64),
        nullable=False,
    )
    evidence_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )
    involved_event_ids_json: Mapped[list[str]] = mapped_column(
        "involved_event_ids",
        JSON,
        nullable=False,
        default=list,
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
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

    timeline: Mapped[InvestigationTimeline] = relationship(back_populates="conflicts")
