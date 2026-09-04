"""API schemas for knowledge graph endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProvenanceItem(BaseModel):
    source_kind: str
    source_id: str
    evidence_id: str | None = None
    finding_id: str | None = None
    timeline_id: str | None = None
    correlation_id: str | None = None
    fusion_id: str | None = None
    ocr_field: str | None = None
    metadata_field: str | None = None
    timestamp: str | None = None
    detail: str | None = None
    engine_version: str | None = None
    policy_version: str | None = None


class GraphEntityResponse(BaseModel):
    id: UUID
    graph_id: UUID
    case_id: UUID
    entity_key: str
    entity_type: str
    display_name: str
    normalized_key: str
    confidence: float
    attributes: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    provenance: list[ProvenanceItem] = Field(default_factory=list)


class GraphRelationshipResponse(BaseModel):
    id: UUID
    graph_id: UUID
    case_id: UUID
    relationship_key: str
    source_entity_key: str
    target_entity_key: str
    relationship_type: str
    confidence: float
    support_count: int
    provenance_count: int
    relationship_weight: float
    creation_source: str
    evidence_ids: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    provenance: list[ProvenanceItem] = Field(default_factory=list)


class KnowledgeGraphResponse(BaseModel):
    id: UUID
    case_id: UUID
    status: str
    entity_count: int
    relationship_count: int
    engine_version: str
    policy_version: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    completed_at: datetime | None = None
    entities: list[GraphEntityResponse] = Field(default_factory=list)
    relationships: list[GraphRelationshipResponse] = Field(default_factory=list)


class GraphEntityListResponse(BaseModel):
    items: list[GraphEntityResponse]
    total: int


class GraphRelationshipListResponse(BaseModel):
    items: list[GraphRelationshipResponse]
    total: int


class NeighborResponse(BaseModel):
    entity: GraphEntityResponse
    relationships: list[GraphRelationshipResponse]
    neighbors: list[GraphEntityResponse]


class GraphPreviewResponse(BaseModel):
    case_id: UUID
    entity_count: int
    relationship_count: int
    entities: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    provenance: dict[str, Any]
    engine_version: str
    policy_version: str
    persisted: bool = False
