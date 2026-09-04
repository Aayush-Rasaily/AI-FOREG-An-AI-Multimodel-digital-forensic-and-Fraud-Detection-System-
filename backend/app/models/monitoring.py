"""SQLAlchemy persistence for Phase 8D monitoring summaries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from backend.app.infrastructure.database.base import Base


class MonitoringSnapshot(Base):
    """Persisted operational dashboard snapshot."""

    __tablename__ = "monitoring_snapshots"
    __table_args__ = (
        Index("ix_monitoring_snapshots_generated_at", "generated_at"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        "payload", JSON, nullable=False, default=dict
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)


class AuditStatistics(Base):
    """Persisted audit analytics summary."""

    __tablename__ = "audit_statistics"
    __table_args__ = (
        Index("ix_audit_statistics_generated_at", "generated_at"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    snapshot_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitoring_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    summary_json: Mapped[dict[str, Any]] = mapped_column(
        "summary", JSON, nullable=False, default=dict
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)


class SystemHealthRecord(Base):
    """Persisted platform health assessment."""

    __tablename__ = "system_health_records"
    __table_args__ = (
        Index("ix_system_health_records_assessed_at", "assessed_at"),
        Index("ix_system_health_records_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    snapshot_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitoring_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(
        "details", JSON, nullable=False, default=dict
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
