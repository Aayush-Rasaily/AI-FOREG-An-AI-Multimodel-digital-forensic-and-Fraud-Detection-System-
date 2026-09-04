"""SQLAlchemy persistence for Phase 9B knowledge graph."""

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


class KnowledgeGraphRun(Base):
    """One persisted knowledge-graph build for a case."""

    __tablename__ = "knowledge_graph_runs"
    __table_args__ = (
        Index("ix_knowledge_graph_runs_case_id", "case_id"),
        Index("ix_knowledge_graph_runs_status", "status"),
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
    entity_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relationship_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance", JSON, nullable=False, default=dict,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )


class GraphEntity(Base):
    """Persisted knowledge-graph entity node."""

    __tablename__ = "graph_entities"
    __table_args__ = (
        Index("ix_graph_entities_graph_id", "graph_id"),
        Index("ix_graph_entities_case_id", "case_id"),
        Index("ix_graph_entities_entity_type", "entity_type"),
        Index("ix_graph_entities_normalized_key", "normalized_key"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    graph_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("knowledge_graph_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_key: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_key: Mapped[str] = mapped_column(String(512), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(
        "attributes", JSON, nullable=False, default=dict,
    )
    evidence_ids_json: Mapped[list] = mapped_column(
        "evidence_ids", JSON, nullable=False, default=list,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class GraphRelationship(Base):
    """Persisted knowledge-graph relationship edge."""

    __tablename__ = "graph_relationships"
    __table_args__ = (
        Index("ix_graph_relationships_graph_id", "graph_id"),
        Index("ix_graph_relationships_case_id", "case_id"),
        Index("ix_graph_relationships_type", "relationship_type"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    graph_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("knowledge_graph_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_key: Mapped[str] = mapped_column(String(128), nullable=False)
    source_entity_key: Mapped[str] = mapped_column(String(128), nullable=False)
    target_entity_key: Mapped[str] = mapped_column(String(128), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    support_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    provenance_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relationship_weight: Mapped[float] = mapped_column(Float, nullable=False)
    creation_source: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_ids_json: Mapped[list] = mapped_column(
        "evidence_ids", JSON, nullable=False, default=list,
    )
    attributes_json: Mapped[dict[str, Any]] = mapped_column(
        "attributes", JSON, nullable=False, default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class GraphEntityAlias(Base):
    """Alternate identifiers / display forms for a graph entity."""

    __tablename__ = "graph_entity_aliases"
    __table_args__ = (
        Index("ix_graph_entity_aliases_graph_id", "graph_id"),
        Index("ix_graph_entity_aliases_entity_key", "entity_key"),
        Index("ix_graph_entity_aliases_alias", "alias"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    graph_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("knowledge_graph_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_key: Mapped[str] = mapped_column(String(128), nullable=False)
    alias: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class GraphProvenance(Base):
    """Provenance rows attached to entities or relationships."""

    __tablename__ = "graph_provenance"
    __table_args__ = (
        Index("ix_graph_provenance_graph_id", "graph_id"),
        Index("ix_graph_provenance_target_key", "target_key"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    graph_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("knowledge_graph_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    target_key: Mapped[str] = mapped_column(String(128), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    finding_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timeline_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fusion_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ocr_field: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_field: Mapped[str | None] = mapped_column(String(128), nullable=True)
    timestamp: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
