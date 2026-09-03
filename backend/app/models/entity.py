"""SQLAlchemy persistence for entity resolution."""

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
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.entities.models import EntityRunStatus, EntityType, RelationshipType
from backend.app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.case import Case


class EntityResolutionRun(Base):
    """One persisted entity-resolution analysis run."""

    __tablename__ = "entity_resolution_runs"
    __table_args__ = (
        Index("ix_entity_resolution_runs_case_id", "case_id"),
        Index(
            "uq_entity_resolution_runs_active",
            "case_id",
            unique=True,
            postgresql_where=text("status IN ('QUEUED', 'RUNNING')"),
            sqlite_where=text("status IN ('QUEUED', 'RUNNING')"),
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
    status: Mapped[EntityRunStatus] = mapped_column(
        Enum(EntityRunStatus, native_enum=False, length=16),
        nullable=False,
    )
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relationship_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    case: Mapped["Case"] = relationship(back_populates="entity_resolution_runs")
    entities: Mapped[list["InvestigationEntityRecord"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
    )
    relationships: Mapped[list["EntityRelationshipRecord"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
    )


class InvestigationEntityRecord(Base):
    """One canonical investigation entity."""

    __tablename__ = "investigation_entities"
    __table_args__ = (
        Index("ix_investigation_entities_analysis_run_id", "analysis_run_id"),
        Index("ix_investigation_entities_case_id", "case_id"),
        Index("ix_investigation_entities_canonical_id", "canonical_id"),
        Index(
            "uq_investigation_entities_run_type_key",
            "analysis_run_id",
            "entity_type",
            "normalized_key",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("entity_resolution_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    canonical_id: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, native_enum=False, length=32),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_key: Mapped[str] = mapped_column(String(512), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    support_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_ids_json: Mapped[list[str]] = mapped_column(
        "evidence_ids",
        JSON,
        nullable=False,
        default=list,
    )
    attributes_json: Mapped[dict[str, Any]] = mapped_column(
        "attributes",
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    analysis_run: Mapped[EntityResolutionRun] = relationship(back_populates="entities")
    support_records: Mapped[list["EntitySupportRecord"]] = relationship(
        back_populates="entity",
        cascade="all, delete-orphan",
        foreign_keys="EntitySupportRecord.entity_id",
    )


class EntityRelationshipRecord(Base):
    """One relationship edge in the investigation graph."""

    __tablename__ = "entity_relationships"
    __table_args__ = (
        Index("ix_entity_relationships_analysis_run_id", "analysis_run_id"),
        Index("ix_entity_relationships_case_id", "case_id"),
        Index(
            "uq_entity_relationships_run_edge",
            "analysis_run_id",
            "source_canonical_id",
            "target_canonical_id",
            "relationship_type",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    analysis_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("entity_resolution_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_id: Mapped[str] = mapped_column(String(256), nullable=False)
    source_canonical_id: Mapped[str] = mapped_column(String(32), nullable=False)
    target_canonical_id: Mapped[str] = mapped_column(String(32), nullable=False)
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, native_enum=False, length=32),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    support_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids_json: Mapped[list[str]] = mapped_column(
        "evidence_ids",
        JSON,
        nullable=False,
        default=list,
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        "provenance",
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

    analysis_run: Mapped[EntityResolutionRun] = relationship(
        back_populates="relationships"
    )
    support_records: Mapped[list["EntitySupportRecord"]] = relationship(
        back_populates="relationship",
        cascade="all, delete-orphan",
        foreign_keys="EntitySupportRecord.relationship_id",
    )


class EntitySupportRecord(Base):
    """Supporting artifact/finding for one entity or relationship."""

    __tablename__ = "entity_support_records"
    __table_args__ = (
        Index("ix_entity_support_records_entity_id", "entity_id"),
        Index("ix_entity_support_records_relationship_id", "relationship_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    entity_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigation_entities.id", ondelete="CASCADE"),
        nullable=True,
    )
    relationship_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("entity_relationships.id", ondelete="CASCADE"),
        nullable=True,
    )
    support_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    support_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    entity: Mapped[InvestigationEntityRecord | None] = relationship(
        back_populates="support_records",
        foreign_keys=[entity_id],
    )
    relationship: Mapped[EntityRelationshipRecord | None] = relationship(
        back_populates="support_records",
        foreign_keys=[relationship_id],
    )
