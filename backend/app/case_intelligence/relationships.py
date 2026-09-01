"""Deterministic cross-evidence relationship detection."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.case_intelligence.models import (
    EvidenceParticipation,
    EvidenceRelationship,
    RelationshipStatus,
    RelationshipType,
)
from backend.app.models.comparison import ComparisonRun
from backend.app.models.evidence import Evidence
from backend.app.models.signature_ai import SignatureVerificationRun


async def detect_relationships(
    session: AsyncSession,
    case_id: UUID,
    participations: tuple[EvidenceParticipation, ...],
) -> tuple[EvidenceRelationship, ...]:
    """Detect relationships only when supported by existing records."""

    evidence_ids = {item.evidence_id for item in participations}
    relationships: list[EvidenceRelationship] = []
    relationships.extend(_duplicate_hash_relationships(participations))
    relationships.extend(
        await _comparison_relationships(session, evidence_ids)
    )
    relationships.extend(
        await _signature_relationships(session, evidence_ids)
    )
    relationships.extend(
        await _shared_metadata_relationships(session, case_id, evidence_ids)
    )
    relationships.extend(_shared_filename_relationships(participations))
    return _deduplicate_relationships(relationships)


def _duplicate_hash_relationships(
    participations: tuple[EvidenceParticipation, ...],
) -> list[EvidenceRelationship]:
    by_hash: dict[str, list[EvidenceParticipation]] = defaultdict(list)
    for item in participations:
        by_hash[item.evidence_hash].append(item)
    results: list[EvidenceRelationship] = []
    for digest, items in sorted(by_hash.items()):
        if len(items) < 2:
            continue
        for index in range(len(items) - 1):
            left = items[index]
            right = items[index + 1]
            results.append(
                EvidenceRelationship(
                    relationship_id=(
                        f"duplicate_hash:{left.evidence_id}:{right.evidence_id}"
                    ),
                    evidence_a_id=left.evidence_id,
                    evidence_b_id=right.evidence_id,
                    relationship_type=RelationshipType.DUPLICATE_HASH,
                    confidence=1.0,
                    supporting_reason="Evidence items share the same SHA-256 hash.",
                    source_reference=f"hash:{digest}",
                    status=RelationshipStatus.CONFIRMED,
                )
            )
    return results


async def _comparison_relationships(
    session: AsyncSession,
    evidence_ids: set[UUID],
) -> list[EvidenceRelationship]:
    rows = list(
        await session.scalars(
            select(ComparisonRun).where(
                ComparisonRun.evidence_id.in_(evidence_ids)
            )
        )
    )
    results: list[EvidenceRelationship] = []
    for row in rows:
        if row.reference_evidence_id is None:
            continue
        if row.reference_evidence_id not in evidence_ids:
            continue
        results.append(
            EvidenceRelationship(
                relationship_id=f"comparison:{row.id}",
                evidence_a_id=row.evidence_id,
                evidence_b_id=row.reference_evidence_id,
                relationship_type=RelationshipType.COMPARISON_LINK,
                confidence=1.0,
                supporting_reason=(
                    "Existing comparison run links questioned and reference evidence."
                ),
                source_reference=f"comparison_run:{row.id}",
                status=RelationshipStatus.CONFIRMED,
            )
        )
    return results


async def _signature_relationships(
    session: AsyncSession,
    evidence_ids: set[UUID],
) -> list[EvidenceRelationship]:
    rows = list(
        await session.scalars(
            select(SignatureVerificationRun).where(
                SignatureVerificationRun.questioned_evidence_id.in_(evidence_ids)
            )
        )
    )
    results: list[EvidenceRelationship] = []
    for row in rows:
        if row.reference_evidence_id not in evidence_ids:
            continue
        if row.questioned_evidence_id is None:
            continue
        results.append(
            EvidenceRelationship(
                relationship_id=f"signature:{row.id}",
                evidence_a_id=row.questioned_evidence_id,
                evidence_b_id=row.reference_evidence_id,
                relationship_type=RelationshipType.SIGNATURE_VERIFICATION_LINK,
                confidence=row.similarity,
                supporting_reason=(
                    "Signature verification run links questioned and "
                    "reference evidence."
                ),
                source_reference=f"signature_verification:{row.id}",
                status=RelationshipStatus.CONFIRMED,
            )
        )
    return results


async def _shared_metadata_relationships(
    session: AsyncSession,
    case_id: UUID,
    evidence_ids: set[UUID],
) -> list[EvidenceRelationship]:
    rows = list(
        await session.scalars(select(Evidence).where(Evidence.case_id == case_id))
    )
    by_creator: dict[str, list[Evidence]] = defaultdict(list)
    for row in rows:
        processing = row.metadata_json.get("processing")
        if not isinstance(processing, dict):
            continue
        creator = processing.get("creator") or processing.get("author")
        if isinstance(creator, str) and creator.strip():
            by_creator[creator.strip().lower()].append(row)
    results: list[EvidenceRelationship] = []
    for creator, items in sorted(by_creator.items()):
        if len(items) < 2:
            continue
        for index in range(len(items) - 1):
            left = items[index]
            right = items[index + 1]
            if left.id not in evidence_ids or right.id not in evidence_ids:
                continue
            results.append(
                EvidenceRelationship(
                    relationship_id=(
                        f"shared_metadata:{left.id}:{right.id}:creator"
                    ),
                    evidence_a_id=left.id,
                    evidence_b_id=right.id,
                    relationship_type=RelationshipType.SHARED_METADATA,
                    confidence=0.8,
                    supporting_reason=f"Shared creator metadata: {creator}.",
                    source_reference="metadata:processing.creator",
                    status=RelationshipStatus.DETECTED,
                )
            )
    return results


def _shared_filename_relationships(
    participations: tuple[EvidenceParticipation, ...],
) -> list[EvidenceRelationship]:
    by_name: dict[str, list[EvidenceParticipation]] = defaultdict(list)
    for item in participations:
        by_name[item.evidence_number.lower()].append(item)
    results: list[EvidenceRelationship] = []
    for name, items in sorted(by_name.items()):
        if len(items) < 2:
            continue
        left = items[0]
        right = items[1]
        results.append(
            EvidenceRelationship(
                relationship_id=f"shared_filename:{left.evidence_id}:{right.evidence_id}",
                evidence_a_id=left.evidence_id,
                evidence_b_id=right.evidence_id,
                relationship_type=RelationshipType.SHARED_FILENAME,
                confidence=0.6,
                supporting_reason=f"Evidence numbers share normalized label '{name}'.",
                source_reference="evidence:evidence_number",
                status=RelationshipStatus.DETECTED,
            )
        )
    return results


def _deduplicate_relationships(
    relationships: list[EvidenceRelationship],
) -> tuple[EvidenceRelationship, ...]:
    seen: set[str] = set()
    unique: list[EvidenceRelationship] = []
    for item in sorted(relationships, key=lambda row: row.relationship_id):
        if item.relationship_id in seen:
            continue
        seen.add(item.relationship_id)
        unique.append(item)
    return tuple(unique)
