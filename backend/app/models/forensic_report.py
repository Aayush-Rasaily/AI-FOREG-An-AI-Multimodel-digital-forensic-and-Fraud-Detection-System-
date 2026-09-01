"""SQLAlchemy persistence for forensic investigation reports."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.infrastructure.database.base import Base
from backend.app.reporting.models import ReportStatus

if TYPE_CHECKING:
    from backend.app.models.case import Case


class ForensicReport(Base):
    """Immutable snapshot of a generated forensic investigation report."""

    __tablename__ = "forensic_reports"
    __table_args__ = (
        Index("ix_forensic_reports_case_id", "case_id"),
        Index(
            "uq_forensic_reports_active",
            "case_id",
            unique=True,
            postgresql_where=text("status IN ('QUEUED', 'GENERATING')"),
            sqlite_where=text("status IN ('QUEUED', 'GENERATING')"),
        ),
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
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, native_enum=False, length=16),
        nullable=False,
    )
    report_version: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    fusion_policy_version: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    case_intelligence_policy_version: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    case_intelligence_run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("case_intelligence_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    evidence_hashes_json: Mapped[list[str]] = mapped_column(
        "evidence_hashes",
        JSON,
        nullable=False,
        default=list,
    )
    content_json: Mapped[dict[str, Any]] = mapped_column(
        "content",
        JSON,
        nullable=False,
        default=dict,
    )
    pdf_storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    pdf_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
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
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    case: Mapped["Case"] = relationship(back_populates="forensic_reports")
