"""SQLAlchemy persistence model for searchable extraction records."""

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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.extraction.models import ExtractionSourceType, ExtractionType
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence
    from backend.app.models.processing import Artifact


class ExtractionRecord(Base):
    """One provenance-preserving extracted text, page, or region."""

    __tablename__ = "extraction_records"
    __table_args__ = (
        Index("ix_extraction_records_evidence_id", "evidence_id"),
        Index("ix_extraction_records_artifact_id", "artifact_id"),
        Index("ix_extraction_records_type", "extraction_type"),
        Index("ix_extraction_records_page_number", "page_number"),
        Index("ix_extraction_records_frame_number", "frame_number"),
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
    artifact_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    extraction_type: Mapped[ExtractionType] = mapped_column(
        Enum(ExtractionType, native_enum=False, length=32),
        nullable=False,
    )
    source_type: Mapped[ExtractionSourceType] = mapped_column(
        Enum(ExtractionSourceType, native_enum=False, length=16),
        nullable=False,
    )
    source_identifier: Mapped[str] = mapped_column(String(1024), nullable=False)
    page_number: Mapped[int | None] = mapped_column(nullable=True)
    frame_number: Mapped[int | None] = mapped_column(nullable=True)
    timestamp_ms: Mapped[int | None] = mapped_column(nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_width: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_width: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    method: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
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

    evidence: Mapped["Evidence"] = relationship(
        back_populates="extraction_records",
    )
    artifact: Mapped["Artifact | None"] = relationship(
        back_populates="extraction_records",
    )
