"""SQLAlchemy persistence for Phase 9E case review.

Table names use the case_review_* prefix to avoid colliding with
Phase 8B/8E review tables.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
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


class CaseReviewRun(Base):
    """One persisted case review / evidence validation run."""

    __tablename__ = "case_review_runs"
    __table_args__ = (
        Index("ix_case_review_runs_case_id", "case_id"),
        Index("ix_case_review_runs_stage", "stage"),
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
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    checklist_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approval_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(
        "metrics",
        JSON,
        nullable=False,
        default=dict,
    )
    outstanding_json: Mapped[list] = mapped_column(
        "outstanding",
        JSON,
        nullable=False,
        default=list,
    )
    blocking_json: Mapped[list] = mapped_column(
        "blocking",
        JSON,
        nullable=False,
        default=list,
    )
    required_roles_json: Mapped[list] = mapped_column(
        "required_roles",
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
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class CaseReviewChecklist(Base):
    """Checklist header for a case review run."""

    __tablename__ = "case_review_checklists"
    __table_args__ = (
        Index("ix_case_review_checklists_run_id", "run_id"),
        Index("ix_case_review_checklists_case_id", "case_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_review_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class CaseReviewChecklistItem(Base):
    """Individual checklist validation item."""

    __tablename__ = "case_review_checklist_items"
    __table_args__ = (
        Index("ix_case_review_checklist_items_checklist_id", "checklist_id"),
        Index("ix_case_review_checklist_items_run_id", "run_id"),
        Index("ix_case_review_checklist_items_case_id", "case_id"),
        Index("ix_case_review_checklist_items_code", "item_code"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    checklist_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_review_checklists.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_review_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_key: Mapped[str] = mapped_column(String(128), nullable=False)
    item_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    suggested_status: Mapped[str] = mapped_column(String(32), nullable=False)
    blocking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    outstanding: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reviewer: Mapped[str | None] = mapped_column(String(256), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
    )


class CaseReviewApproval(Base):
    """Explicit multi-role approval record (never auto-generated)."""

    __tablename__ = "case_review_approvals"
    __table_args__ = (
        Index("ix_case_review_approvals_run_id", "run_id"),
        Index("ix_case_review_approvals_case_id", "case_id"),
        Index("ix_case_review_approvals_role", "approver_role"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_review_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    checklist_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_review_checklists.id", ondelete="SET NULL"),
        nullable=True,
    )
    checklist_item_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_review_checklist_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer: Mapped[str] = mapped_column(String(256), nullable=False)
    approver_role: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    comments: Mapped[str] = mapped_column(Text, nullable=False, default="")
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
    )


class CaseReviewValidationRecord(Base):
    """Persisted validation metrics snapshot for a review run."""

    __tablename__ = "case_review_validation_records"
    __table_args__ = (
        Index("ix_case_review_validation_records_run_id", "run_id"),
        Index("ix_case_review_validation_records_case_id", "case_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_review_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    validation_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence_coverage_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    review_completion_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    approval_completion_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    outstanding_issues: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    blocking_issues: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(
        "metrics",
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
    )
