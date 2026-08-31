"""SQLAlchemy persistence model for stored evidence metadata."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.domain.evidence import EvidenceStatus
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.case import Case
    from backend.app.models.custody import ChainOfCustodyEvent


class Evidence(Base):
    """Immutable-original evidence metadata associated with one case."""

    __tablename__ = "evidence"
    __table_args__ = (
        UniqueConstraint("evidence_number", name="uq_evidence_number"),
        UniqueConstraint("case_id", "sha256_hash", name="uq_evidence_case_hash"),
        Index("ix_evidence_case_id", "case_id"),
        Index("ix_evidence_sha256_hash", "sha256_hash"),
        Index("ix_evidence_created_at", "created_at"),
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
        index=False,
    )
    evidence_number: Mapped[str] = mapped_column(String(32), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[EvidenceStatus] = mapped_column(
        Enum(EvidenceStatus, native_enum=False, length=32),
        nullable=False,
        default=EvidenceStatus.REGISTERED,
    )
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    case: Mapped["Case"] = relationship(back_populates="evidence")
    custody_events: Mapped[list["ChainOfCustodyEvent"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChainOfCustodyEvent.timestamp",
    )
