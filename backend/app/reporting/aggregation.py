"""Collect structured data for forensic investigation reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.case_intelligence.aggregation import collect_case_evidence
from backend.app.case_intelligence.repository import CaseIntelligenceRepository
from backend.app.correlation.repository import CorrelationRepository
from backend.app.entities.repository import EntityRepository
from backend.app.forensics.repository import ForensicRepository
from backend.app.fusion.repository import FusionRepository
from backend.app.models.case import Case
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.evidence import Evidence
from backend.app.models.fusion import FusionAnalysisRun, JuryAssessmentRecord
from backend.app.models.timeline import InvestigationTimeline


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _serialize_jury(member: JuryAssessmentRecord) -> dict[str, Any]:
    return {
        "role": member.role.value,
        "member_name": member.member_name,
        "verdict": member.verdict.value,
        "confidence": member.confidence,
        "availability": member.availability.value,
        "supporting_finding_ids": list(member.supporting_finding_ids),
        "contradictory_finding_ids": list(member.contradictory_finding_ids),
        "explanation": member.explanation,
        "limitations": member.limitations,
        "model_name": member.model_name,
        "model_version": member.model_version,
        "ai_generated": True,
    }


def _serialize_fusion(run: FusionAnalysisRun) -> dict[str, Any]:
    metadata = run.metadata_json
    return {
        "fusion_run_id": str(run.id),
        "status": run.status.value,
        "engine_version": run.engine_version,
        "policy_version": run.policy_version,
        "verdict": run.verdict.value if run.verdict else None,
        "risk_score": run.risk_score,
        "confidence": run.confidence,
        "findings_count": run.findings_count,
        "conflicts_count": run.conflicts_count,
        "completed_at": _serialize_datetime(run.completed_at),
        "modality_status": list(run.modality_status_json),
        "jury_assessments": [_serialize_jury(item) for item in run.jury_assessments],
        "conflicts": [
            {
                "conflict_id": item.conflict_id,
                "conflict_type": item.conflict_type.value,
                "severity": item.severity.value,
                "involved_finding_ids": list(item.involved_finding_ids),
                "involved_modalities": list(item.involved_modalities),
                "explanation": item.explanation,
                "resolution_status": item.resolution_status.value,
            }
            for item in run.conflicts
        ],
        "agreement": metadata.get("agreement"),
        "explanation": metadata.get("explanation"),
        "limitations": metadata.get("limitations"),
        "supporting_finding_ids": list(metadata.get("supporting_finding_ids", [])),
        "contradictory_finding_ids": list(
            metadata.get("contradictory_finding_ids", [])
        ),
        "provenance": run.provenance_json,
        "ai_generated": True,
    }


def _serialize_custody(event: ChainOfCustodyEvent) -> dict[str, Any]:
    return {
        "event_id": str(event.id),
        "event_type": event.event_type.value,
        "timestamp": _serialize_datetime(event.timestamp),
        "actor_type": event.actor_type.value,
        "actor_id": event.actor_id,
        "description": event.description,
        "metadata": event.metadata_json,
    }


def _serialize_finding(finding: Any) -> dict[str, Any]:
    return {
        "finding_id": str(finding.id),
        "category": finding.category.value,
        "severity": finding.severity.value,
        "confidence": finding.confidence,
        "description": finding.description,
        "detector": finding.detector,
        "explanation": finding.explanation,
    }


async def aggregate_report_data(
    session: AsyncSession,
    case: Case,
) -> dict[str, Any]:
    """Collect a stable snapshot of all report source data."""

    fusion_repository = FusionRepository(session)
    forensic_repository = ForensicRepository(session)
    intelligence_repository = CaseIntelligenceRepository(session)

    evidence_rows = list(
        await session.scalars(
            select(Evidence)
            .where(Evidence.case_id == case.id)
            .options(selectinload(Evidence.custody_events))
            .order_by(Evidence.created_at, Evidence.evidence_number)
        )
    )
    participations = await collect_case_evidence(session, case.id)
    participation_by_evidence = {
        item.evidence_id: item for item in participations
    }

    evidence_items: list[dict[str, Any]] = []
    fusion_snapshots: list[dict[str, Any]] = []
    analysis_summaries: list[dict[str, Any]] = []

    for evidence in evidence_rows:
        participation = participation_by_evidence.get(evidence.id)
        fusion_run = await fusion_repository.get_latest_for_evidence(evidence.id)
        forensic_run = await forensic_repository.latest_run_for_evidence(evidence.id)
        findings: list[dict[str, Any]] = []
        if forensic_run is not None:
            forensic_findings, _ = await forensic_repository.list_findings_for_evidence(
                evidence.id,
                limit=100,
                offset=0,
            )
            findings = [_serialize_finding(item) for item in forensic_findings]

        processing = evidence.metadata_json.get("processing", {})
        if not isinstance(processing, dict):
            processing = {}

        evidence_items.append(
            {
                "evidence_id": str(evidence.id),
                "evidence_number": evidence.evidence_number,
                "filename": evidence.original_filename,
                "mime_type": evidence.mime_type,
                "file_size": evidence.file_size,
                "sha256_hash": evidence.sha256_hash,
                "status": evidence.status.value,
                "ingested_at": _serialize_datetime(evidence.created_at),
                "updated_at": _serialize_datetime(evidence.updated_at),
                "coverage_status": (
                    participation.coverage_status.value
                    if participation
                    else "not_analyzed"
                ),
                "fusion_verdict": (
                    participation.fusion_verdict.value
                    if participation and participation.fusion_verdict
                    else None
                ),
                "risk_score": participation.risk_score if participation else None,
                "confidence": participation.confidence if participation else None,
                "custody_events": [
                    _serialize_custody(item) for item in evidence.custody_events
                ],
                "processing_status": processing.get("status"),
            }
        )
        if fusion_run is not None:
            fusion_snapshots.append(
                {
                    "evidence_id": str(evidence.id),
                    "evidence_number": evidence.evidence_number,
                    **_serialize_fusion(fusion_run),
                }
            )
        analysis_summaries.append(
            {
                "evidence_id": str(evidence.id),
                "evidence_number": evidence.evidence_number,
                "evidence_type": (
                    participation.evidence_type if participation else "unknown"
                ),
                "forensic_findings": findings,
                "forensic_run_id": (
                    str(forensic_run.id) if forensic_run is not None else None
                ),
                "image_ai": evidence.metadata_json.get("image_ai"),
                "document_ai": evidence.metadata_json.get("document_ai"),
                "signature_ai": evidence.metadata_json.get("signature_ai"),
                "video_ai": evidence.metadata_json.get("video_ai"),
                "audio_ai": evidence.metadata_json.get("audio_ai"),
                "comparison": evidence.metadata_json.get("reference_comparison"),
            }
        )

    intelligence_run = await intelligence_repository.get_latest_for_case(case.id)
    case_intelligence: dict[str, Any] | None = None
    if intelligence_run is not None:
        case_intelligence = {
            "analysis_run_id": str(intelligence_run.id),
            "status": intelligence_run.status.value,
            "engine_version": intelligence_run.engine_version,
            "policy_version": intelligence_run.policy_version,
            "verdict": (
                intelligence_run.verdict.value if intelligence_run.verdict else None
            ),
            "risk_score": intelligence_run.risk_score,
            "confidence": intelligence_run.confidence,
            "coverage": intelligence_run.coverage_json,
            "participations": [
                {
                    "evidence_id": str(item.evidence_id),
                    "evidence_number": item.evidence_number,
                    "coverage_status": item.coverage_status,
                    "fusion_verdict": (
                        item.fusion_verdict.value if item.fusion_verdict else None
                    ),
                    "risk_score": item.risk_score,
                    "confidence": item.confidence,
                }
                for item in intelligence_run.participations
            ],
            "relationships": [
                {
                    "relationship_id": item.relationship_id,
                    "relationship_type": item.relationship_type.value,
                    "evidence_a_id": str(item.evidence_a_id),
                    "evidence_b_id": str(item.evidence_b_id),
                    "confidence": item.confidence,
                    "supporting_reason": item.supporting_reason,
                    "source_reference": item.source_reference,
                    "status": item.status.value,
                }
                for item in intelligence_run.relationships
            ],
            "conflicts": [
                {
                    "conflict_id": item.conflict_id,
                    "conflict_type": item.conflict_type.value,
                    "severity": item.severity.value,
                    "involved_evidence_ids": list(item.involved_evidence_ids),
                    "involved_finding_ids": list(item.involved_finding_ids),
                    "explanation": item.explanation,
                    "resolution_status": item.resolution_status.value,
                }
                for item in intelligence_run.conflicts
            ],
            "timeline": [
                {
                    "event_id": item.event_id,
                    "event_type": item.event_type.value,
                    "timestamp": _serialize_datetime(item.timestamp),
                    "timestamp_known": item.timestamp_known,
                    "evidence_id": (
                        str(item.evidence_id) if item.evidence_id else None
                    ),
                    "source_reference": item.source_reference,
                    "description": item.description,
                }
                for item in intelligence_run.timeline_events
            ],
            "explanation": intelligence_run.metadata_json.get("explanation"),
            "limitations": intelligence_run.metadata_json.get("limitations"),
            "supporting_evidence_ids": list(
                intelligence_run.metadata_json.get("supporting_evidence_ids", [])
            ),
            "contradictory_evidence_ids": list(
                intelligence_run.metadata_json.get("contradictory_evidence_ids", [])
            ),
            "provenance": intelligence_run.provenance_json,
        }

    # --- Correlation (Phase 7B) ---
    correlation_repo = CorrelationRepository(session)
    correlation_run = await correlation_repo.get_latest_for_case(
        case.id,
    )
    correlation_snapshot: dict[str, Any] | None = None
    if correlation_run is not None:
        corr_records = sorted(
            correlation_run.correlations,
            key=lambda c: (
                str(c.left_evidence_id),
                str(c.right_evidence_id),
            ),
        )
        correlation_snapshot = {
            "run_id": str(correlation_run.id),
            "status": correlation_run.status.value,
            "engine_version": correlation_run.engine_version,
            "policy_version": correlation_run.policy_version,
            "correlation_count": (
                correlation_run.correlation_count
            ),
            "items": [
                {
                    "left_evidence_id": str(
                        c.left_evidence_id,
                    ),
                    "right_evidence_id": str(
                        c.right_evidence_id,
                    ),
                    "correlation_type": (
                        c.correlation_type.value
                        if hasattr(c.correlation_type, "value")
                        else str(c.correlation_type)
                    ),
                    "score": c.score,
                    "confidence": c.confidence,
                    "explanation": c.explanation,
                }
                for c in corr_records
            ],
        }

    # --- Entity Resolution (Phase 7C) ---
    entity_repo = EntityRepository(session)
    entity_run = await entity_repo.get_latest_for_case(case.id)
    entity_snapshot: dict[str, Any] | None = None
    if entity_run is not None:
        entity_run_detail = await entity_repo.get_run_with_details(
            entity_run.id,
        )
        if entity_run_detail is not None:
            entities_list = sorted(
                entity_run_detail.entities,
                key=lambda e: e.canonical_id,
            )
            relationships_list = sorted(
                entity_run_detail.relationships,
                key=lambda r: (
                    r.source_canonical_id,
                    r.target_canonical_id,
                ),
            )
            entity_snapshot = {
                "run_id": str(entity_run.id),
                "status": entity_run.status.value,
                "engine_version": entity_run.engine_version,
                "entity_count": entity_run.entity_count,
                "relationship_count": entity_run.relationship_count,
                "entities": [
                    {
                        "canonical_id": e.canonical_id,
                        "entity_type": e.entity_type,
                        "display_name": e.display_name,
                        "confidence": e.confidence,
                        "support_count": e.support_count,
                    }
                    for e in entities_list
                ],
                "relationships": [
                    {
                        "source": r.source_canonical_id,
                        "target": r.target_canonical_id,
                        "type": r.relationship_type,
                        "confidence": r.confidence,
                    }
                    for r in relationships_list
                ],
            }

    # --- Timeline (Phase 7A) ---
    timeline_run = await session.scalars(
        select(InvestigationTimeline)
        .where(InvestigationTimeline.case_id == case.id)
        .order_by(InvestigationTimeline.created_at.desc())
        .limit(1)
    )
    timeline_row = timeline_run.first()
    timeline_snapshot: dict[str, Any] | None = None
    if timeline_row is not None:
        from sqlalchemy.orm import selectinload as _sel

        timeline_full = await session.get(
            InvestigationTimeline,
            timeline_row.id,
            options=[_sel(InvestigationTimeline.events)],
        )
        if timeline_full is not None:
            events_sorted = sorted(
                timeline_full.events,
                key=lambda ev: (
                    ev.timestamp.isoformat() if ev.timestamp else "",
                    ev.event_id,
                ),
            )
            timeline_snapshot = {
                "run_id": str(timeline_full.id),
                "status": timeline_full.status.value,
                "event_count": timeline_full.event_count,
                "items": [
                    {
                        "event_id": ev.event_id,
                        "event_type": ev.event_type.value,
                        "timestamp": _serialize_datetime(
                            ev.timestamp,
                        ),
                        "evidence_id": (
                            str(ev.evidence_id)
                            if ev.evidence_id
                            else None
                        ),
                        "description": ev.description,
                    }
                    for ev in events_sorted
                ],
            }

    return {
        "case": {
            "case_id": str(case.id),
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": case.status.value,
            "priority": case.priority.value,
            "created_at": _serialize_datetime(case.created_at),
            "updated_at": _serialize_datetime(case.updated_at),
        },
        "evidence": evidence_items,
        "evidence_hashes": [item["sha256_hash"] for item in evidence_items],
        "analysis_summaries": analysis_summaries,
        "fusion_snapshots": fusion_snapshots,
        "case_intelligence": case_intelligence,
        "correlation": correlation_snapshot,
        "entity_resolution": entity_snapshot,
        "timeline": timeline_snapshot,
    }
