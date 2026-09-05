"""SQLAlchemy persistence for Phase 9D decision support.

Table names are prefixed to avoid colliding with Phase 8E workflow_tasks.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from backend.app.infrastructure.database.base import Base


class DecisionSupportRun(Base):
    """One persisted decision-support / investigator-workflow plan."""

    __tablename__ = "decision_support_runs"
    __table_args__ = (
        Index("ix_decision_support_runs_case_id", "case_id"),
        Index("ix_decision_support_runs_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(32), nullable=False)
    task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(
        "metrics", JSON, nullable=False, default=dict,
    )
    open_conflicts_json: Mapped[list] = mapped_column(
        "open_conflicts", JSON, nullable=False, default=list,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance", JSON, nullable=False, default=dict,
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )


class DecisionSupportTask(Base):
    """Persisted investigator workflow task."""

    __tablename__ = "decision_support_tasks"
    __table_args__ = (
        Index("ix_decision_support_tasks_run_id", "run_id"),
        Index("ix_decision_support_tasks_case_id", "case_id"),
        Index("ix_decision_support_tasks_status", "status"),
        Index("ix_decision_support_tasks_stage", "stage"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("decision_support_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_key: Mapped[str] = mapped_column(String(128), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    estimated_effort_hours: Mapped[float] = mapped_column(Float, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    required_evidence_ids_json: Mapped[list] = mapped_column(
        "required_evidence_ids", JSON, nullable=False, default=list,
    )
    supporting_intelligence_json: Mapped[dict[str, Any]] = mapped_column(
        "supporting_intelligence", JSON, nullable=False, default=dict,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance", JSON, nullable=False, default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class DecisionSupportReviewItem(Base):
    """Persisted evidence review-queue item."""

    __tablename__ = "decision_support_review_items"
    __table_args__ = (
        Index("ix_decision_support_review_items_run_id", "run_id"),
        Index("ix_decision_support_review_items_case_id", "case_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("decision_support_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    queue_key: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_id: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasons_json: Mapped[list] = mapped_column(
        "reasons", JSON, nullable=False, default=list,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance", JSON, nullable=False, default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class DecisionSupportDecision(Base):
    """Persisted investigator decision log entry."""

    __tablename__ = "decision_support_decisions"
    __table_args__ = (
        Index("ix_decision_support_decisions_case_id", "case_id"),
        Index("ix_decision_support_decisions_task_id", "task_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("decision_support_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    task_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("decision_support_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision_type: Mapped[str] = mapped_column(String(64), nullable=False)
    investigator: Mapped[str] = mapped_column(String(256), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance", JSON, nullable=False, default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
