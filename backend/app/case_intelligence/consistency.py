"""Cross-evidence consistency analysis."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.case_intelligence.models import (
    CaseConflict,
    CaseConflictType,
    ConflictResolutionStatus,
    EvidenceParticipation,
)
from backend.app.forensics.models import Severity
from backend.app.models.custody import ChainOfCustodyEvent


async def analyze_consistency(
    session: AsyncSession,
    case_id: UUID,
    participations: tuple[EvidenceParticipation, ...],
) -> tuple[CaseConflict, ...]:
    """Record consistency issues only when existing metadata supports them."""

    conflicts: list[CaseConflict] = []
    conflicts.extend(_metadata_timestamp_conflicts(participations))
    conflicts.extend(await _custody_provenance_conflicts(session, participations))
    return tuple(conflicts)


def _metadata_timestamp_conflicts(
    participations: tuple[EvidenceParticipation, ...],
) -> list[CaseConflict]:
    rows: list[tuple[UUID, datetime, str]] = []
    for item in participations:
        if item.fusion_completed_at is not None:
            rows.append(
                (item.evidence_id, item.fusion_completed_at, "fusion_completed_at")
            )
    if len(rows) < 2:
        return []
    rows.sort(key=lambda row: row[1])
    earliest = rows[0]
    latest = rows[-1]
    delta_seconds = abs((latest[1] - earliest[1]).total_seconds())
    if delta_seconds <= 86_400:
        return []
    return [
        CaseConflict(
            conflict_id=(
                f"temporal:{earliest[0]}:{latest[0]}:{earliest[2]}:{latest[2]}"
            ),
            involved_evidence_ids=(earliest[0], latest[0]),
            involved_finding_ids=(),
            conflict_type=CaseConflictType.TEMPORAL_INCONSISTENCY,
            severity=Severity.MEDIUM,
            explanation=(
                "Fusion completion timestamps differ by more than 24 hours across "
                "evidence items."
            ),
            resolution_status=ConflictResolutionStatus.OPEN,
        )
    ]


async def _custody_provenance_conflicts(
    session: AsyncSession,
    participations: tuple[EvidenceParticipation, ...],
) -> list[CaseConflict]:
    evidence_ids = [item.evidence_id for item in participations]
    if not evidence_ids:
        return []
    custody_rows = list(
        await session.scalars(
            select(ChainOfCustodyEvent).where(
                ChainOfCustodyEvent.evidence_id.in_(evidence_ids)
            )
        )
    )
    hashes_by_evidence: dict[UUID, set[str]] = {}
    for event in custody_rows:
        digest = event.metadata_json.get("sha256_hash")
        if isinstance(digest, str):
            hashes_by_evidence.setdefault(event.evidence_id, set()).add(digest)
    conflicts: list[CaseConflict] = []
    for item in participations:
        custody_hashes = hashes_by_evidence.get(item.evidence_id, set())
        if not custody_hashes:
            continue
        if item.evidence_hash not in custody_hashes and len(custody_hashes) > 0:
            conflicts.append(
                CaseConflict(
                    conflict_id=f"provenance:{item.evidence_id}",
                    involved_evidence_ids=(item.evidence_id,),
                    involved_finding_ids=(),
                    conflict_type=CaseConflictType.PROVENANCE_INCONSISTENCY,
                    severity=Severity.HIGH,
                    explanation=(
                        "Custody metadata hash does not match current evidence hash."
                    ),
                    resolution_status=ConflictResolutionStatus.OPEN,
                )
            )
    return conflicts
