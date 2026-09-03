"""Pydantic schemas for entity resolution APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.entities.models import EntityRunStatus, EntityType, RelationshipType


class EntitySupportResponse(BaseModel):
    """One supporting artifact or finding."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    support_kind: str
    support_ref: str
    label: str
    value: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CanonicalEntityResponse(BaseModel):
    """One canonical investigation entity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_run_id: UUID
    case_id: UUID
    canonical_id: str
    entity_type: EntityType
    display_name: str
    normalized_key: str
    confidence: float
    support_count: int
    evidence_ids: list[UUID] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    supports: list[EntitySupportResponse] = Field(default_factory=list)
    created_at: datetime


class EntityRelationshipResponse(BaseModel):
    """One directed relationship between canonical entities."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_run_id: UUID
    case_id: UUID
    relationship_id: str
    source_canonical_id: str
    target_canonical_id: str
    relationship_type: RelationshipType
    confidence: float
    support_count: int
    explanation: str
    evidence_ids: list[UUID] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    supports: list[EntitySupportResponse] = Field(default_factory=list)
    created_at: datetime


class InvestigationGraphResponse(BaseModel):
    """Investigation graph payload."""

    nodes: list[CanonicalEntityResponse] = Field(default_factory=list)
    edges: list[EntityRelationshipResponse] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityRunResponse(BaseModel):
    """Summary of one entity-resolution analysis run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    status: EntityRunStatus
    engine_version: str
    policy_version: str
    entity_count: int
    relationship_count: int
    evidence_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)


class EntityDetailResponse(EntityRunResponse):
    """Entity-resolution run with entities, relationships, and graph."""

    entities: list[CanonicalEntityResponse] = Field(default_factory=list)
    relationships: list[EntityRelationshipResponse] = Field(default_factory=list)
    graph: InvestigationGraphResponse


class EntityRunListResponse(BaseModel):
    """Paginated entity-resolution history for one case."""

    items: list[EntityRunResponse]
    total: int
    limit: int
    offset: int
