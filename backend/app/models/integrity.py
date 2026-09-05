"""SQLAlchemy persistence for Phase 9F integrity monitoring."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from backend.app.infrastructure.database.base import Base


class IntegrityMonitorRun(Base):
    """One persisted integrity monitoring run for a case."""

    __tablename__ = "integrity_monitor_runs"
    __table_args__ = (
        Index("ix_integrity_monitor_runs_case_id", "case_id"),
        Index("ix_integrity_monitor_runs_status", "status"),
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
    check_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alert_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    drift_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(
        "metrics",
        JSON,
        nullable=False,
        default=dict,
    )
    timeline_json: Mapped[list] = mapped_column(
        "timeline",
        JSON,
        nullable=False,
        default=list,
    )
    fingerprints_json: Mapped[dict[str, Any]] = mapped_column(
        "fingerprints",
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


class IntegrityCheck(Base):
    """Individual integrity check outcome."""

    __tablename__ = "integrity_checks"
    __table_args__ = (
        Index("ix_integrity_checks_run_id", "run_id"),
        Index("ix_integrity_checks_case_id", "case_id"),
        Index("ix_integrity_checks_code", "check_code"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("integrity_monitor_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    check_key: Mapped[str] = mapped_column(String(128), nullable=False)
    check_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    evidence_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    expected: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class IntegrityAlert(Base):
    """Integrity alert derived from failed/warned checks."""

    __tablename__ = "integrity_alerts"
    __table_args__ = (
        Index("ix_integrity_alerts_run_id", "run_id"),
        Index("ix_integrity_alerts_case_id", "case_id"),
        Index("ix_integrity_alerts_severity", "severity"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("integrity_monitor_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    alert_key: Mapped[str] = mapped_column(String(128), nullable=False)
    alert_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    check_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
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


class IntegrityDriftRecord(Base):
    """Detected drift vs prior integrity snapshot."""

    __tablename__ = "integrity_drift_records"
    __table_args__ = (
        Index("ix_integrity_drift_records_run_id", "run_id"),
        Index("ix_integrity_drift_records_case_id", "case_id"),
        Index("ix_integrity_drift_records_evidence_id", "evidence_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("integrity_monitor_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    drift_key: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_id: Mapped[str] = mapped_column(String(64), nullable=False)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance",
        JSON,
        nullable=False,
        default=dict,
    )
    integrity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
