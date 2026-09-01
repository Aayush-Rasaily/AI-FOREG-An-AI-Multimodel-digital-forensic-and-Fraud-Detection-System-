"""Deterministic case-level risk and verdict policy."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.case_intelligence.conflicts import detect_case_conflicts
from backend.app.case_intelligence.consistency import analyze_consistency
from backend.app.case_intelligence.coverage import compute_coverage
from backend.app.case_intelligence.models import (
    CaseAssessment,
    CaseConflict,
    CaseIntelligenceResult,
    CaseIntelligenceRunStatus,
    EvidenceCoverage,
    EvidenceCoverageStatus,
    EvidenceParticipation,
    EvidenceRelationship,
    TimelineEvent,
)
from backend.app.case_intelligence.relationships import detect_relationships
from backend.app.case_intelligence.timeline import build_timeline
from backend.app.fusion.models import FusionVerdict

ENGINE_VERSION = "1.0"
POLICY_VERSION = "1.0"

_SUSPICIOUS = frozenset({FusionVerdict.SUSPICIOUS, FusionVerdict.POTENTIAL_FRAUD})
_FRAUD = frozenset({FusionVerdict.POTENTIAL_FRAUD})


async def synthesize_case(
    *,
    session: AsyncSession,
    case_id: UUID,
    case_number: str,
    participations: tuple[EvidenceParticipation, ...],
) -> CaseIntelligenceResult:
    """
    Case risk policy v1.0:
    - Weight evidence by fusion risk score and confidence when available.
    - Boost case risk when multiple evidence items are suspicious.
    - Apply conflict penalty without treating unavailable as negative.
    - Inconclusive evidence does not increase fraud risk.
    - Weak single evidence cannot dominate when stronger contradictory evidence exists.
    """

    relationships = await detect_relationships(session, case_id, participations)
    consistency_conflicts = await analyze_consistency(session, case_id, participations)
    conflicts = detect_case_conflicts(participations, consistency_conflicts)
    coverage = compute_coverage(participations, open_conflicts=len(conflicts))
    timeline = await build_timeline(session, case_id, participations, conflicts)
    if not participations:
        return CaseIntelligenceResult(
            status=CaseIntelligenceRunStatus.SUCCEEDED,
            assessment=_insufficient_assessment(
                case_id=case_id,
                case_number=case_number,
                participations=participations,
                relationships=relationships,
                conflicts=conflicts,
                timeline=timeline,
                coverage=coverage,
            ),
            metadata={"evidence_count": 0},
        )
    risk_score = _case_risk_score(participations, conflicts)
    confidence = _case_confidence(participations)
    verdict = _case_verdict(participations, conflicts, coverage)
    supporting_ids = tuple(
        item.evidence_id
        for item in participations
        if item.fusion_verdict in _SUSPICIOUS
    )
    contradictory_ids = tuple(
        item.evidence_id
        for item in participations
        if item.fusion_verdict == FusionVerdict.GENUINE
    )
    assessment = CaseAssessment(
        verdict=verdict,
        risk_score=risk_score,
        confidence=confidence,
        status=CaseIntelligenceRunStatus.SUCCEEDED,
        coverage=coverage,
        participations=participations,
        relationships=relationships,
        conflicts=conflicts,
        timeline=timeline,
        supporting_evidence_ids=supporting_ids,
        contradictory_evidence_ids=contradictory_ids,
        explanation=_build_explanation(
            verdict=verdict,
            coverage=coverage,
            conflicts=conflicts,
            supporting_ids=supporting_ids,
        ),
        limitations=(
            "Case synthesis aggregates Phase 6F fusion results; unavailable or "
            "unanalyzed evidence is not treated as negative proof."
        ),
        provenance={
            "case_id": str(case_id),
            "case_number": case_number,
            "evidence_count": len(participations),
            "policy_version": POLICY_VERSION,
            "fusion_runs": [
                {
                    "evidence_id": str(item.evidence_id),
                    "fusion_run_id": str(item.fusion_run_id)
                    if item.fusion_run_id
                    else None,
                }
                for item in participations
            ],
        },
        engine_version=ENGINE_VERSION,
        policy_version=POLICY_VERSION,
    )
    return CaseIntelligenceResult(
        status=CaseIntelligenceRunStatus.SUCCEEDED,
        assessment=assessment,
        metadata={
            "evidence_count": len(participations),
            "relationship_count": len(relationships),
            "conflict_count": len(conflicts),
        },
    )


def _case_risk_score(
    participations: tuple[EvidenceParticipation, ...],
    conflicts: tuple[CaseConflict, ...],
) -> float | None:
    scored = [
        (item.risk_score or 0.0) * (item.confidence or 0.5)
        for item in participations
        if item.fusion_verdict in _SUSPICIOUS and item.risk_score is not None
    ]
    if not scored:
        return None
    base = sum(scored) / len(scored)
    multiplier = 1.0 + min(0.2 * max(len(scored) - 1, 0), 0.4)
    penalty = min(0.15 * len(conflicts), 0.3)
    return round(min(max(base * multiplier - penalty * 100, 0.0), 100.0), 2)


def _case_confidence(
    participations: tuple[EvidenceParticipation, ...],
) -> float | None:
    values = [
        item.confidence
        for item in participations
        if item.confidence is not None
        and item.coverage_status == EvidenceCoverageStatus.ANALYZED
    ]
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _case_verdict(
    participations: tuple[EvidenceParticipation, ...],
    conflicts: tuple[CaseConflict, ...],
    coverage: EvidenceCoverage,
) -> FusionVerdict:
    if coverage.total_evidence == 0:
        return FusionVerdict.INSUFFICIENT_EVIDENCE
    analyzed = [
        item for item in participations if item.fusion_verdict is not None
    ]
    if not analyzed:
        return FusionVerdict.INSUFFICIENT_EVIDENCE
    if all(
        item.coverage_status == EvidenceCoverageStatus.UNAVAILABLE
        for item in participations
    ):
        return FusionVerdict.UNAVAILABLE
    fraud_count = sum(1 for item in analyzed if item.fusion_verdict in _FRAUD)
    suspicious_count = sum(
        1 for item in analyzed if item.fusion_verdict == FusionVerdict.SUSPICIOUS
    )
    genuine_count = sum(
        1 for item in analyzed if item.fusion_verdict == FusionVerdict.GENUINE
    )
    if fraud_count >= 2 or (fraud_count >= 1 and suspicious_count >= 1):
        return FusionVerdict.POTENTIAL_FRAUD
    if fraud_count >= 1:
        return FusionVerdict.POTENTIAL_FRAUD
    if suspicious_count >= 2:
        return FusionVerdict.SUSPICIOUS
    if suspicious_count >= 1 and genuine_count >= 1:
        return FusionVerdict.INCONCLUSIVE
    if suspicious_count >= 1:
        return FusionVerdict.SUSPICIOUS
    if genuine_count >= 1 and not conflicts:
        return FusionVerdict.GENUINE
    if coverage.inconclusive > 0 or coverage.not_analyzed > 0:
        return FusionVerdict.INCONCLUSIVE
    return FusionVerdict.INCONCLUSIVE


def _build_explanation(
    *,
    verdict: FusionVerdict,
    coverage: EvidenceCoverage,
    conflicts: tuple[CaseConflict, ...],
    supporting_ids: tuple[UUID, ...],
) -> str:
    conflict_note = (
        f" {len(conflicts)} open case conflict(s) recorded."
        if conflicts
        else ""
    )
    return (
        f"Case verdict: {verdict.value}.{conflict_note} "
        f"Analyzed {coverage.analyzed}/{coverage.total_evidence} evidence items; "
        f"{len(supporting_ids)} supporting suspicious/potential-fraud item(s)."
    )


def _insufficient_assessment(
    *,
    case_id: UUID,
    case_number: str,
    participations: tuple[EvidenceParticipation, ...],
    relationships: tuple[EvidenceRelationship, ...],
    conflicts: tuple[CaseConflict, ...],
    timeline: tuple[TimelineEvent, ...],
    coverage: EvidenceCoverage,
) -> CaseAssessment:
    return CaseAssessment(
        verdict=FusionVerdict.INSUFFICIENT_EVIDENCE,
        risk_score=None,
        confidence=None,
        status=CaseIntelligenceRunStatus.SUCCEEDED,
        coverage=coverage,
        participations=participations,
        relationships=relationships,
        conflicts=conflicts,
        timeline=timeline,
        supporting_evidence_ids=(),
        contradictory_evidence_ids=(),
        explanation="No evidence available for case-level synthesis.",
        limitations="Register and analyze evidence before running case intelligence.",
        provenance={
            "case_id": str(case_id),
            "case_number": case_number,
            "evidence_count": 0,
            "policy_version": POLICY_VERSION,
        },
        engine_version=ENGINE_VERSION,
        policy_version=POLICY_VERSION,
    )
