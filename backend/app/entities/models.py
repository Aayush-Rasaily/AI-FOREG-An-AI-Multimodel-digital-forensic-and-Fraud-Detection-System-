"""Domain models for entity resolution and investigation graphs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID


class EntityRunStatus(StrEnum):
    """Lifecycle states for one entity-resolution analysis run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class EntityType(StrEnum):
    """Canonical investigation entity types supported by Phase 7C."""

    PERSON = "person"
    ORGANIZATION = "organization"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    WEBSITE = "website"
    DOMAIN = "domain"
    DEVICE = "device"
    CAMERA = "camera"
    VEHICLE = "vehicle"
    BANK_ACCOUNT = "bank_account"
    CRYPTO_WALLET = "crypto_wallet"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    QR_CODE = "qr_code"
    LOGO = "logo"
    SIGNATURE = "signature"
    LOCATION = "location"
    IP_ADDRESS = "ip_address"
    FILE_HASH = "file_hash"


class RelationshipType(StrEnum):
    """Deterministic investigation-graph relationship types."""

    OWNS = "owns"
    USES = "uses"
    CREATED = "created"
    CONTAINS = "contains"
    REFERENCES = "references"
    SENT_TO = "sent_to"
    RECEIVED_FROM = "received_from"
    CAPTURED_BY = "captured_by"
    SIGNED_BY = "signed_by"
    LOCATED_AT = "located_at"
    RELATED_TO = "related_to"
    DERIVED_FROM = "derived_from"
    DUPLICATE_OF = "duplicate_of"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"


@dataclass(frozen=True)
class EntitySupport:
    """One supporting artifact or finding behind an entity or edge."""

    support_kind: str
    support_id: str
    label: str
    value: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalEntity:
    """One merged canonical investigation entity."""

    canonical_id: str
    case_id: UUID
    entity_type: EntityType
    display_name: str
    normalized_key: str
    confidence: float
    support_count: int
    evidence_ids: tuple[UUID, ...] = ()
    supports: tuple[EntitySupport, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityEdge:
    """One directed relationship between two canonical entities."""

    relationship_id: str
    case_id: UUID
    source_canonical_id: str
    target_canonical_id: str
    relationship_type: RelationshipType
    confidence: float
    explanation: str
    support_count: int
    evidence_ids: tuple[UUID, ...] = ()
    supports: tuple[EntitySupport, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InvestigationGraph:
    """Serialized investigation graph for one resolution run."""

    nodes: tuple[CanonicalEntity, ...]
    edges: tuple[EntityEdge, ...]
    provenance: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EntityBuildResult:
    """Engine output for one entity-resolution analysis."""

    entities: tuple[CanonicalEntity, ...]
    relationships: tuple[EntityEdge, ...]
    graph: InvestigationGraph
    provenance: dict[str, Any]
    metadata: dict[str, Any]
