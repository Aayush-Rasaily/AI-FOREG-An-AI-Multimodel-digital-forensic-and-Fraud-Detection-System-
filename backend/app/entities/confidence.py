"""Deterministic confidence helpers for entity resolution."""

from __future__ import annotations

from backend.app.entities.models import EntityType, RelationshipType
from backend.app.entities.policy import (
    CONFIDENCE_ADDRESS,
    CONFIDENCE_BANK_ACCOUNT,
    CONFIDENCE_CAMERA,
    CONFIDENCE_CREATOR,
    CONFIDENCE_CRYPTO_WALLET,
    CONFIDENCE_DEVICE,
    CONFIDENCE_DOCUMENT_ID,
    CONFIDENCE_DOMAIN,
    CONFIDENCE_EMAIL,
    CONFIDENCE_FILE_HASH,
    CONFIDENCE_IP,
    CONFIDENCE_LOCATION,
    CONFIDENCE_LOGO,
    CONFIDENCE_MEDIA,
    CONFIDENCE_PHONE,
    CONFIDENCE_QR,
    CONFIDENCE_RELATIONSHIP_DEFAULT,
    CONFIDENCE_SIGNATURE,
    CONFIDENCE_WEBSITE,
)

_ENTITY_CONFIDENCE: dict[EntityType, float] = {
    EntityType.FILE_HASH: CONFIDENCE_FILE_HASH,
    EntityType.EMAIL: CONFIDENCE_EMAIL,
    EntityType.PHONE: CONFIDENCE_PHONE,
    EntityType.QR_CODE: CONFIDENCE_QR,
    EntityType.SIGNATURE: CONFIDENCE_SIGNATURE,
    EntityType.LOCATION: CONFIDENCE_LOCATION,
    EntityType.CAMERA: CONFIDENCE_CAMERA,
    EntityType.DEVICE: CONFIDENCE_DEVICE,
    EntityType.IP_ADDRESS: CONFIDENCE_IP,
    EntityType.DOMAIN: CONFIDENCE_DOMAIN,
    EntityType.WEBSITE: CONFIDENCE_WEBSITE,
    EntityType.CRYPTO_WALLET: CONFIDENCE_CRYPTO_WALLET,
    EntityType.BANK_ACCOUNT: CONFIDENCE_BANK_ACCOUNT,
    EntityType.DOCUMENT: CONFIDENCE_MEDIA,
    EntityType.IMAGE: CONFIDENCE_MEDIA,
    EntityType.VIDEO: CONFIDENCE_MEDIA,
    EntityType.AUDIO: CONFIDENCE_MEDIA,
    EntityType.LOGO: CONFIDENCE_LOGO,
    EntityType.PERSON: CONFIDENCE_CREATOR,
    EntityType.ORGANIZATION: CONFIDENCE_CREATOR,
    EntityType.ADDRESS: CONFIDENCE_ADDRESS,
    EntityType.VEHICLE: CONFIDENCE_DEVICE,
}


_RELATIONSHIP_CONFIDENCE: dict[RelationshipType, float] = {
    RelationshipType.DUPLICATE_OF: CONFIDENCE_FILE_HASH,
    RelationshipType.DERIVED_FROM: CONFIDENCE_FILE_HASH,
    RelationshipType.CONTAINS: CONFIDENCE_EMAIL,
    RelationshipType.REFERENCES: CONFIDENCE_DOCUMENT_ID,
    RelationshipType.CAPTURED_BY: CONFIDENCE_CAMERA,
    RelationshipType.USES: CONFIDENCE_DEVICE,
    RelationshipType.SIGNED_BY: CONFIDENCE_SIGNATURE,
    RelationshipType.LOCATED_AT: CONFIDENCE_LOCATION,
    RelationshipType.CREATED: CONFIDENCE_CREATOR,
    RelationshipType.RELATED_TO: CONFIDENCE_RELATIONSHIP_DEFAULT,
    RelationshipType.SUPPORTS: CONFIDENCE_RELATIONSHIP_DEFAULT,
    RelationshipType.CONTRADICTS: CONFIDENCE_RELATIONSHIP_DEFAULT,
    RelationshipType.OWNS: CONFIDENCE_RELATIONSHIP_DEFAULT,
    RelationshipType.SENT_TO: CONFIDENCE_EMAIL,
    RelationshipType.RECEIVED_FROM: CONFIDENCE_EMAIL,
}


def confidence_for_entity(entity_type: EntityType) -> float:
    return _ENTITY_CONFIDENCE.get(entity_type, CONFIDENCE_RELATIONSHIP_DEFAULT)


def confidence_for_relationship(relationship_type: RelationshipType) -> float:
    return _RELATIONSHIP_CONFIDENCE.get(
        relationship_type,
        CONFIDENCE_RELATIONSHIP_DEFAULT,
    )


def boost_confidence(base: float, support_count: int) -> float:
    """Slight deterministic boost for multi-evidence support, capped at 1.0."""

    if support_count <= 1:
        return round(base, 4)
    bonus = min(0.04, 0.01 * (support_count - 1))
    return round(min(1.0, base + bonus), 4)
