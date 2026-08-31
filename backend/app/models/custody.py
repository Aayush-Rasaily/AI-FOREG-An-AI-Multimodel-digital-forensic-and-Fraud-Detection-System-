"""SQLAlchemy persistence model for chain-of-custody events."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.domain.custody import CustodyActorType, CustodyEventType
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence


class ChainOfCustodyEvent(Base):
    """Append-only record describing an evidence custody transition."""

    __tablename__ = "chain_of_custody_events"
    __table_args__ = (
        Index("ix_custody_evidence_id", "evidence_id"),
        Index("ix_custody_timestamp", "timestamp"),
    )

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
    event_type: Mapped[CustodyEventType] = mapped_column(
        Enum(CustodyEventType, native_enum=False, length=64),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    actor_type: Mapped[CustodyActorType] = mapped_column(
        Enum(CustodyActorType, native_enum=False, length=16),
        nullable=False,
    )
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

    evidence: Mapped["Evidence"] = relationship(back_populates="custody_events")
