"""Domain models for the investigation knowledge graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID


class GraphRunStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class GraphEntityType(StrEnum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    DEVICE = "DEVICE"
    FILE = "FILE"
    DOCUMENT = "DOCUMENT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOMAIN = "DOMAIN"
    URL = "URL"
    IP_ADDRESS = "IP_ADDRESS"
    LOCATION = "LOCATION"
    CASE = "CASE"
    EVIDENCE = "EVIDENCE"
    TIMELINE_EVENT = "TIMELINE_EVENT"
    AI_FINDING = "AI_FINDING"
    SIGNATURE = "SIGNATURE"
    HASH = "HASH"
    CAMERA = "CAMERA"
    SOCIAL_ACCOUNT = "SOCIAL_ACCOUNT"
    LICENSE_PLATE = "LICENSE_PLATE"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    CRYPTO_WALLET = "CRYPTO_WALLET"


class GraphRelationshipType(StrEnum):
    USES_DEVICE = "USES_DEVICE"
    OWNS = "OWNS"
    CREATED = "CREATED"
    SENT = "SENT"
    RECEIVED = "RECEIVED"
    LOCATED_AT = "LOCATED_AT"
    CAPTURED_BY = "CAPTURED_BY"
    REFERENCES = "REFERENCES"
    DERIVED_FROM = "DERIVED_FROM"
    SIMILAR_TO = "SIMILAR_TO"
    CORRELATED_WITH = "CORRELATED_WITH"
    SHARES_IDENTIFIER = "SHARES_IDENTIFIER"
    MENTIONS = "MENTIONS"
    CONNECTED_TO = "CONNECTED_TO"
    PART_OF = "PART_OF"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    OBSERVED_AT = "OBSERVED_AT"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"


@dataclass(frozen=True)
class GraphProvenanceRef:
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


@dataclass
class CandidateEntity:
    """Pre-resolution entity candidate extracted from investigation outputs."""

    entity_type: GraphEntityType
    display_name: str
    normalized_key: str
    identity_keys: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[GraphProvenanceRef, ...] = ()


@dataclass
class ResolvedEntity:
    """Canonical entity after deterministic resolution."""

    entity_id: str
    entity_type: GraphEntityType
    display_name: str
    normalized_key: str
    aliases: tuple[str, ...] = ()
    confidence: float = 1.0
    attributes: dict[str, Any] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[GraphProvenanceRef, ...] = ()


@dataclass
class GraphEdge:
    """Directed relationship between resolved entities."""

    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: GraphRelationshipType
    confidence: float
    support_count: int
    provenance_count: int
    relationship_weight: float
    creation_source: str
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[GraphProvenanceRef, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraphResult:
    """In-memory knowledge graph for one case build."""

    case_id: UUID
    entities: list[ResolvedEntity]
    relationships: list[GraphEdge]
    provenance_summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
