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
    from backend.app.models.audio_ai import AudioAIFinding, AudioAnalysisRun
    from backend.app.models.case import Case
    from backend.app.models.comparison import (
        ComparisonRun,
        Difference,
        ReferenceEvidence,
    )
    from backend.app.models.custody import ChainOfCustodyEvent
    from backend.app.models.document_ai import DocumentAIFinding, DocumentAnalysisRun
    from backend.app.models.extraction import ExtractionRecord
    from backend.app.models.forensics import AnalysisRun, Finding
    from backend.app.models.fusion import FusionAnalysisRun
    from backend.app.models.image_ai import ImageAIFinding, ImageAnalysisRun
    from backend.app.models.processing import Artifact, ProcessingJob
    from backend.app.models.signature_ai import SignatureVerificationRun
    from backend.app.models.video_ai import VideoAIFinding, VideoAnalysisRun


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
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProcessingJob.created_at",
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Artifact.created_at",
    )
    extraction_records: Mapped[list["ExtractionRecord"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ExtractionRecord.created_at",
    )
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AnalysisRun.created_at",
    )
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Finding.created_at",
    )
    image_analysis_runs: Mapped[list["ImageAnalysisRun"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ImageAnalysisRun.created_at",
    )
    image_ai_findings: Mapped[list["ImageAIFinding"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ImageAIFinding.created_at",
    )
    document_analysis_runs: Mapped[list["DocumentAnalysisRun"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DocumentAnalysisRun.created_at",
    )
    document_ai_findings: Mapped[list["DocumentAIFinding"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DocumentAIFinding.created_at",
    )
    signature_reference_runs: Mapped[list["SignatureVerificationRun"]] = relationship(
        back_populates="reference_evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="SignatureVerificationRun.reference_evidence_id",
        order_by="SignatureVerificationRun.created_at",
    )
    signature_questioned_runs: Mapped[list["SignatureVerificationRun"]] = relationship(
        back_populates="questioned_evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="SignatureVerificationRun.questioned_evidence_id",
        order_by="SignatureVerificationRun.created_at",
    )
    video_analysis_runs: Mapped[list["VideoAnalysisRun"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="VideoAnalysisRun.created_at",
    )
    video_ai_findings: Mapped[list["VideoAIFinding"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="VideoAIFinding.created_at",
    )
    audio_analysis_runs: Mapped[list["AudioAnalysisRun"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="AudioAnalysisRun.evidence_id",
        order_by="AudioAnalysisRun.created_at",
    )
    audio_ai_findings: Mapped[list["AudioAIFinding"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AudioAIFinding.created_at",
    )
    reference_records: Mapped[list["ReferenceEvidence"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="ReferenceEvidence.evidence_id",
    )
    comparison_runs: Mapped[list["ComparisonRun"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="ComparisonRun.evidence_id",
        order_by="ComparisonRun.created_at",
    )
    differences: Mapped[list["Difference"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Difference.created_at",
    )
    fusion_analysis_runs: Mapped[list["FusionAnalysisRun"]] = relationship(
        back_populates="evidence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="FusionAnalysisRun.created_at",
    )
