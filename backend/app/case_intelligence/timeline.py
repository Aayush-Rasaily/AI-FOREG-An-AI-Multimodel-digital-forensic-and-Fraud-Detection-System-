"""Deterministic case timeline generation."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.case_intelligence.models import (
    CaseConflict,
    EvidenceParticipation,
    TimelineEvent,
    TimelineEventType,
)
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.evidence import Evidence


async def build_timeline(
    session: AsyncSession,
    case_id: UUID,
    participations: tuple[EvidenceParticipation, ...],
    conflicts: tuple[CaseConflict, ...],
) -> tuple[TimelineEvent, ...]:
    """Build a deterministic timeline from known timestamps only."""

    events: list[TimelineEvent] = []
    evidence_rows = list(
        await session.scalars(select(Evidence).where(Evidence.case_id == case_id))
    )
    for evidence in evidence_rows:
        events.append(
            TimelineEvent(
                event_id=f"registered:{evidence.id}",
                event_type=TimelineEventType.EVIDENCE_REGISTERED,
                timestamp=evidence.created_at,
                timestamp_known=True,
                evidence_id=evidence.id,
                source_reference=f"evidence:{evidence.id}",
                description=f"Evidence {evidence.evidence_number} registered.",
            )
        )
        processing = evidence.metadata_json.get("processing")
        if isinstance(processing, dict) and processing.get("status") == "SUCCEEDED":
            events.append(
                TimelineEvent(
                    event_id=f"processed:{evidence.id}",
                    event_type=TimelineEventType.EVIDENCE_PROCESSED,
                    timestamp=evidence.updated_at,
                    timestamp_known=True,
                    evidence_id=evidence.id,
                    source_reference="metadata:processing",
                    description=f"Evidence {evidence.evidence_number} processed.",
                )
            )
        comparison = evidence.metadata_json.get("reference_comparison")
        if isinstance(comparison, dict) and comparison.get("status") == "SUCCEEDED":
            events.append(
                TimelineEvent(
                    event_id=f"comparison:{evidence.id}",
                    event_type=TimelineEventType.COMPARISON_COMPLETED,
                    timestamp=evidence.updated_at,
                    timestamp_known=True,
                    evidence_id=evidence.id,
                    source_reference="metadata:reference_comparison",
                    description=(
                        "Reference comparison completed for "
                        f"{evidence.evidence_number}."
                    ),
                )
            )
    for item in participations:
        if item.fusion_completed_at is not None:
            events.append(
                TimelineEvent(
                    event_id=f"fusion:{item.fusion_run_id}",
                    event_type=TimelineEventType.FUSION_COMPLETED,
                    timestamp=item.fusion_completed_at,
                    timestamp_known=True,
                    evidence_id=item.evidence_id,
                    source_reference=(
                        f"fusion_analysis_run:{item.fusion_run_id}"
                        if item.fusion_run_id
                        else f"evidence:{item.evidence_id}"
                    ),
                    description=(
                        f"Phase 6F fusion completed for {item.evidence_number}."
                    ),
                    metadata={
                        "verdict": item.fusion_verdict.value
                        if item.fusion_verdict
                        else None
                    },
                )
            )
    custody_rows = list(
        await session.scalars(
            select(ChainOfCustodyEvent).where(
                ChainOfCustodyEvent.evidence_id.in_(
                    [item.evidence_id for item in participations]
                )
            )
        )
    )
    for event in custody_rows:
        events.append(
            TimelineEvent(
                event_id=f"custody:{event.id}",
                event_type=TimelineEventType.CUSTODY_EVENT,
                timestamp=event.timestamp,
                timestamp_known=True,
                evidence_id=event.evidence_id,
                source_reference=f"chain_of_custody:{event.id}",
                description=f"Custody event: {event.event_type.value}.",
                metadata=event.metadata_json,
            )
        )
    for conflict in conflicts:
        if conflict.conflict_type.value == "temporal_inconsistency":
            events.append(
                TimelineEvent(
                    event_id=f"timeline_conflict:{conflict.conflict_id}",
                    event_type=TimelineEventType.TEMPORAL_INCONSISTENCY,
                    timestamp=None,
                    timestamp_known=False,
                    evidence_id=conflict.involved_evidence_ids[0]
                    if conflict.involved_evidence_ids
                    else None,
                    source_reference=conflict.conflict_id,
                    description=conflict.explanation,
                )
            )
    return _sort_timeline(events)


def _sort_timeline(events: list[TimelineEvent]) -> tuple[TimelineEvent, ...]:
    return tuple(
        sorted(
            events,
            key=lambda item: (
                item.timestamp is None,
                item.timestamp or item.event_id,
                item.event_id,
            ),
        )
    )
