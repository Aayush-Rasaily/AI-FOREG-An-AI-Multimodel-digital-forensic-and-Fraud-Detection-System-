"""SQLAlchemy persistence model for investigation cases."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.domain.case import CasePriority, CaseStatus
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.case_intelligence import CaseIntelligenceRun
    from backend.app.models.comparison import ReferenceEvidence
    from backend.app.models.evidence import Evidence
    from backend.app.models.forensic_report import ForensicReport


class Case(Base):
    """An investigation container that owns evidence and custody history."""

    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_status", "status"),
        Index("ix_cases_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    case_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, native_enum=False, length=32),
        nullable=False,
        default=CaseStatus.OPEN,
    )
    priority: Mapped[CasePriority] = mapped_column(
        Enum(CasePriority, native_enum=False, length=16),
        nullable=False,
        default=CasePriority.MEDIUM,
    )
    created_by: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="SYSTEM",
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

    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reference_evidence: Mapped[list["ReferenceEvidence"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    case_intelligence_runs: Mapped[list["CaseIntelligenceRun"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CaseIntelligenceRun.created_at",
    )
    forensic_reports: Mapped[list["ForensicReport"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ForensicReport.created_at",
    )
