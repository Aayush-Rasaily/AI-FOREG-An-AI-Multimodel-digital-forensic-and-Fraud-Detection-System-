"""SQLAlchemy persistence for investigation intelligence summaries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from backend.app.infrastructure.database.base import Base


class InvestigationSummary(Base):
    """Persisted investigation intelligence narrative snapshot."""

    __tablename__ = "investigation_summaries"
    __table_args__ = (
        Index("ix_investigation_summaries_case_id", "case_id"),
        Index("ix_investigation_summaries_generated_at", "generated_at"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    overall_risk: Mapped[str] = mapped_column(String(16), nullable=False)
    overall_confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    overview_json: Mapped[dict[str, Any]] = mapped_column(
        "overview", JSON, nullable=False, default=dict
    )
    key_findings_json: Mapped[list[Any]] = mapped_column(
        "key_findings", JSON, nullable=False, default=list
    )
    timeline_summary_json: Mapped[dict[str, Any]] = mapped_column(
        "timeline_summary", JSON, nullable=False, default=dict
    )
    correlation_summary_json: Mapped[dict[str, Any]] = mapped_column(
        "correlation_summary", JSON, nullable=False, default=dict
    )
    ai_summary_json: Mapped[dict[str, Any]] = mapped_column(
        "ai_summary", JSON, nullable=False, default=dict
    )
    recommendations_json: Mapped[list[Any]] = mapped_column(
        "recommendations", JSON, nullable=False, default=list
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance", JSON, nullable=False, default=dict
    )
    narrative_json: Mapped[list[Any]] = mapped_column(
        "narrative", JSON, nullable=False, default=list
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
