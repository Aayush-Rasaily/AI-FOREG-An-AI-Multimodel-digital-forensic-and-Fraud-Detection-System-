"""SQLAlchemy persistence for Phase 9H platform validation."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from backend.app.infrastructure.database.base import Base


class PlatformValidationRun(Base):
    """One persisted platform validation execution."""

    __tablename__ = "platform_validation_runs"
    __table_args__ = (Index("ix_platform_validation_runs_status", "status"),)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    readiness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    readiness_level: Mapped[str] = mapped_column(String(32), nullable=False)
    check_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pass_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary_json: Mapped[dict[str, Any]] = mapped_column(
        "summary",
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


class PlatformValidationResult(Base):
    """Individual check result for a validation run."""

    __tablename__ = "platform_validation_results"
    __table_args__ = (
        Index("ix_platform_validation_results_run_id", "run_id"),
        Index("ix_platform_validation_results_check_key", "check_key"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("platform_validation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    check_key: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    details_json: Mapped[dict[str, Any]] = mapped_column(
        "details",
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class PlatformValidationIssue(Base):
    """Non-passing issue derived from a validation run."""

    __tablename__ = "platform_validation_issues"
    __table_args__ = (
        Index("ix_platform_validation_issues_run_id", "run_id"),
        Index("ix_platform_validation_issues_severity", "severity"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("platform_validation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    check_key: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    details_json: Mapped[dict[str, Any]] = mapped_column(
        "details",
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
