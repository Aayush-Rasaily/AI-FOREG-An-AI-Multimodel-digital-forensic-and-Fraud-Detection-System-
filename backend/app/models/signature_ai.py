"""SQLAlchemy persistence models for signature verification."""

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

from backend.app.ai.document.signature.schemas import SignatureVerdict
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.evidence import Evidence
    from backend.app.models.processing import Artifact


class SignatureVerificationRun(Base):
    """One signature verification execution."""

    __tablename__ = "signature_verification_runs"
    __table_args__ = (
        Index(
            "ix_signature_verification_runs_questioned_evidence_id",
            "questioned_evidence_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    reference_evidence_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )
    questioned_evidence_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="SET NULL"),
        nullable=True,
    )
    processing_job_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processing_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    reference_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    questioned_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[SignatureVerdict] = mapped_column(
        Enum(SignatureVerdict, native_enum=False, length=16),
        nullable=False,
    )
    device: Mapped[str] = mapped_column(String(16), nullable=False, default="cpu")
    processing_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    artifact_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    localization_json: Mapped[dict[str, Any] | None] = mapped_column(
        "localization",
        JSON,
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    reference_evidence: Mapped["Evidence | None"] = relationship(
        foreign_keys=[reference_evidence_id],
        back_populates="signature_reference_runs",
    )
    questioned_evidence: Mapped["Evidence | None"] = relationship(
        foreign_keys=[questioned_evidence_id],
        back_populates="signature_questioned_runs",
    )
    artifact: Mapped["Artifact | None"] = relationship(foreign_keys=[artifact_id])
