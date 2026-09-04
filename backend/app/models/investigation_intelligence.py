"""SQLAlchemy persistence for Phase 9C investigation intelligence."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from backend.app.infrastructure.database.base import Base


class InvestigationIntelligenceRun(Base):
    """One persisted investigation-intelligence analysis run."""

    __tablename__ = "investigation_intelligence_runs"
    __table_args__ = (
        Index("ix_investigation_intelligence_runs_case_id", "case_id"),
        Index("ix_investigation_intelligence_runs_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    investigation_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
    )
    overall_completeness: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
    )
    hypothesis_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    gap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recommendation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    open_conflict_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    coverage_json: Mapped[dict[str, Any]] = mapped_column(
        "coverage", JSON, nullable=False, default=dict,
    )
    open_conflicts_json: Mapped[list] = mapped_column(
        "open_conflicts", JSON, nullable=False, default=list,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance", JSON, nullable=False, default=dict,
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )


class InvestigationHypothesis(Base):
    """Persisted investigative hypothesis."""

    __tablename__ = "investigation_hypotheses"
    __table_args__ = (
        Index("ix_investigation_hypotheses_run_id", "run_id"),
        Index("ix_investigation_hypotheses_case_id", "case_id"),
        Index("ix_investigation_hypotheses_type", "hypothesis_type"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigation_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    hypothesis_key: Mapped[str] = mapped_column(String(128), nullable=False)
    hypothesis_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    supporting_evidence_ids_json: Mapped[list] = mapped_column(
        "supporting_evidence_ids", JSON, nullable=False, default=list,
    )
    contradicting_evidence_ids_json: Mapped[list] = mapped_column(
        "contradicting_evidence_ids", JSON, nullable=False, default=list,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance", JSON, nullable=False, default=dict,
    )
    attributes_json: Mapped[dict[str, Any]] = mapped_column(
        "attributes", JSON, nullable=False, default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class EvidenceGapRecordRow(Base):
    """Persisted evidence-gap record."""

    __tablename__ = "evidence_gap_records"
    __table_args__ = (
        Index("ix_evidence_gap_records_run_id", "run_id"),
        Index("ix_evidence_gap_records_case_id", "case_id"),
        Index("ix_evidence_gap_records_gap_type", "gap_type"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigation_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    gap_key: Mapped[str] = mapped_column(String(128), nullable=False)
    gap_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(64), nullable=False)
    affected_evidence_ids_json: Mapped[list] = mapped_column(
        "affected_evidence_ids", JSON, nullable=False, default=list,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance", JSON, nullable=False, default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class InvestigationRecommendation(Base):
    """Persisted investigation recommendation."""

    __tablename__ = "investigation_recommendations"
    __table_args__ = (
        Index("ix_investigation_recommendations_run_id", "run_id"),
        Index("ix_investigation_recommendations_case_id", "case_id"),
        Index("ix_investigation_recommendations_code", "code"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigation_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    recommendation_key: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    action_text: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    related_hypothesis_keys_json: Mapped[list] = mapped_column(
        "related_hypothesis_keys", JSON, nullable=False, default=list,
    )
    related_gap_keys_json: Mapped[list] = mapped_column(
        "related_gap_keys", JSON, nullable=False, default=list,
    )
    affected_evidence_ids_json: Mapped[list] = mapped_column(
        "affected_evidence_ids", JSON, nullable=False, default=list,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance", JSON, nullable=False, default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
