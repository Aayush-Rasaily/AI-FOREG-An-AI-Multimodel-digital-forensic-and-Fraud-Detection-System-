"""SQLAlchemy persistence model for audit events."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.infrastructure.database.base import Base


class AuditEvent(Base):
    """Immutable audit trail record."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_timestamp", "timestamp"),
        Index("ix_audit_events_case_id", "case_id"),
        Index("ix_audit_events_evidence_id", "evidence_id"),
        Index("ix_audit_events_operation", "operation"),
        Index("ix_audit_events_category", "category"),
        Index("ix_audit_events_user", "user"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    user: Mapped[str] = mapped_column(
        String(256), nullable=False, default="system",
    )
    operation: Mapped[str] = mapped_column(
        String(128), nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(64), nullable=False,
    )
    case_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True,
    )
    evidence_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True,
    )
    previous_state_json: Mapped[Any | None] = mapped_column(
        "previous_state", JSON, nullable=True,
    )
    new_state_json: Mapped[Any | None] = mapped_column(
        "new_state", JSON, nullable=True,
    )
    client_ip: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(512), nullable=True,
    )
    engine_version: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    policy_version: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    sha256_checksum: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
    )
    integrity_hash: Mapped[str] = mapped_column(
        String(64), nullable=False,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict,
    )
