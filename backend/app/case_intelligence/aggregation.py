"""Aggregate Phase 6F fusion results for all evidence in a case."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.case_intelligence.models import (
    EvidenceCoverageStatus,
    EvidenceParticipation,
)
from backend.app.domain.evidence import EvidenceStatus
from backend.app.fusion.models import FusionRunStatus, FusionVerdict
from backend.app.fusion.repository import FusionRepository
from backend.app.models.evidence import Evidence


def _evidence_type(evidence: Evidence) -> str:
    classification = evidence.metadata_json.get("classification")
    if isinstance(classification, str) and classification:
        return classification.lower()
    return evidence.mime_type.split("/", maxsplit=1)[0]


def _coverage_status(
    evidence: Evidence,
    fusion_verdict: FusionVerdict | None,
    fusion_status: FusionRunStatus | None,
) -> EvidenceCoverageStatus:
    if fusion_status == FusionRunStatus.FAILED:
        return EvidenceCoverageStatus.FAILED
    if fusion_status == FusionRunStatus.UNAVAILABLE:
        return EvidenceCoverageStatus.UNAVAILABLE
    if fusion_verdict is None:
        if evidence.status in {
            EvidenceStatus.REGISTERED,
            EvidenceStatus.READY_FOR_ANALYSIS,
        }:
            return EvidenceCoverageStatus.NOT_ANALYZED
        return EvidenceCoverageStatus.NOT_ANALYZED
    if fusion_verdict == FusionVerdict.INSUFFICIENT_EVIDENCE:
        return EvidenceCoverageStatus.INSUFFICIENT_EVIDENCE
    if fusion_verdict == FusionVerdict.UNAVAILABLE:
        return EvidenceCoverageStatus.UNAVAILABLE
    if fusion_verdict == FusionVerdict.INCONCLUSIVE:
        return EvidenceCoverageStatus.INCONCLUSIVE
    return EvidenceCoverageStatus.ANALYZED


async def collect_case_evidence(
    session: AsyncSession,
    case_id: UUID,
) -> tuple[EvidenceParticipation, ...]:
    """Collect latest Phase 6F fusion results for every evidence item."""

    fusion_repository = FusionRepository(session)
    evidence_rows = list(
        await session.scalars(
            select(Evidence)
            .where(Evidence.case_id == case_id)
            .order_by(Evidence.created_at, Evidence.evidence_number)
        )
    )
    participations: list[EvidenceParticipation] = []
    for evidence in evidence_rows:
        fusion_run = await fusion_repository.get_latest_for_evidence(evidence.id)
        fusion_meta = evidence.metadata_json.get("multimodal_fusion", {})
        if fusion_run is None:
            participations.append(
                EvidenceParticipation(
                    evidence_id=evidence.id,
                    evidence_number=evidence.evidence_number,
                    evidence_type=_evidence_type(evidence),
                    evidence_hash=evidence.sha256_hash,
                    evidence_status=evidence.status.value,
                    coverage_status=_coverage_status(evidence, None, None),
                    fusion_run_id=None,
                    fusion_verdict=None,
                    risk_score=None,
                    confidence=None,
                    supporting_finding_ids=(),
                    contradictory_finding_ids=(),
                    conflicts_count=0,
                    participating_modalities=(),
                    unavailable_modalities=(),
                    fusion_engine_version=None,
                    fusion_policy_version=None,
                    fusion_completed_at=None,
                    reason="No Phase 6F fusion analysis exists for this evidence.",
                )
            )
            continue
        metadata = fusion_run.metadata_json
        participations.append(
            EvidenceParticipation(
                evidence_id=evidence.id,
                evidence_number=evidence.evidence_number,
                evidence_type=_evidence_type(evidence),
                evidence_hash=evidence.sha256_hash,
                evidence_status=evidence.status.value,
                coverage_status=_coverage_status(
                    evidence,
                    fusion_run.verdict,
                    fusion_run.status,
                ),
                fusion_run_id=fusion_run.id,
                fusion_verdict=fusion_run.verdict,
                risk_score=fusion_run.risk_score,
                confidence=fusion_run.confidence,
                supporting_finding_ids=tuple(
                    metadata.get("supporting_finding_ids", [])
                ),
                contradictory_finding_ids=tuple(
                    metadata.get("contradictory_finding_ids", [])
                ),
                conflicts_count=fusion_run.conflicts_count,
                participating_modalities=tuple(
                    metadata.get("participating_modalities", [])
                ),
                unavailable_modalities=tuple(
                    metadata.get("unavailable_modalities", [])
                ),
                fusion_engine_version=fusion_run.engine_version,
                fusion_policy_version=fusion_run.policy_version,
                fusion_completed_at=fusion_run.completed_at,
                reason=(
                    None
                    if fusion_run.status == FusionRunStatus.SUCCEEDED
                    else fusion_run.error_message
                ),
            )
        )
        _ = fusion_meta
    return tuple(participations)
