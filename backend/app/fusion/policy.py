"""Deterministic evidence fusion policy."""

from __future__ import annotations

from uuid import UUID

from backend.app.forensics.models import Severity
from backend.app.fusion.agreement import compute_agreement
from backend.app.fusion.conflicts import detect_conflicts
from backend.app.fusion.jury import assess_jury
from backend.app.fusion.models import (
    FindingVerdict,
    FusionAssessment,
    FusionConflict,
    FusionResult,
    FusionRunStatus,
    FusionVerdict,
    JuryAssessment,
    ModalityAvailability,
    ModalityStatus,
    NormalizedFinding,
)

ENGINE_VERSION = "1.0"
POLICY_VERSION = "1.0"

_SEVERITY_WEIGHT = {
    Severity.CRITICAL: 1.0,
    Severity.HIGH: 0.8,
    Severity.MEDIUM: 0.5,
    Severity.LOW: 0.3,
    Severity.INFO: 0.1,
}


def fuse_evidence(
    *,
    evidence_id: UUID,
    source_hash: str,
    findings: tuple[NormalizedFinding, ...],
    modality_statuses: tuple[ModalityStatus, ...],
) -> FusionResult:
    """
    Fusion policy:
    - Weight findings by severity; multiply by confidence when present.
    - Exclude unavailable findings from risk scoring.
    - Jury senior judge verdict informs final verdict with conflict penalty.
    - Unavailable modalities never reduce confidence as negative evidence.
  """

    if not findings:
        return FusionResult(
            status=FusionRunStatus.SUCCEEDED,
            assessment=_insufficient_assessment(
                evidence_id=evidence_id,
                source_hash=source_hash,
                findings=findings,
                modality_statuses=modality_statuses,
                jury_assessments=(),
                conflicts=(),
            ),
            normalized_findings=findings,
            modality_statuses=modality_statuses,
            metadata={"findings_count": 0},
        )
    jury_assessments = assess_jury(findings)
    conflicts = detect_conflicts(findings, jury_assessments)
    agreement = compute_agreement(findings, modality_statuses, jury_assessments)
    risk_score = _risk_score(findings)
    senior = next(
        (item for item in jury_assessments if item.role.value == "senior_judge"),
        None,
    )
    verdict = senior.verdict if senior else FusionVerdict.INCONCLUSIVE
    if conflicts and verdict == FusionVerdict.GENUINE:
        verdict = FusionVerdict.INCONCLUSIVE
    confidence = _fusion_confidence(findings, jury_assessments, agreement)
    supporting = tuple(
        item.finding_id
        for item in findings
        if item.verdict
        in {
            FindingVerdict.SUPPORTS_SUSPICIOUS,
            FindingVerdict.SUPPORTS_FRAUD,
        }
    )
    contradictory = tuple(
        item.finding_id
        for item in findings
        if item.verdict == FindingVerdict.SUPPORTS_GENUINE
    )
    participating = tuple(
        status.modality
        for status in modality_statuses
        if status.availability == ModalityAvailability.AVAILABLE
        and status.findings_count > 0
    )
    unavailable = tuple(
        status.modality
        for status in modality_statuses
        if status.availability
        in {
            ModalityAvailability.UNAVAILABLE,
            ModalityAvailability.FAILED,
        }
    )
    assessment = FusionAssessment(
        verdict=verdict,
        risk_score=risk_score,
        confidence=confidence,
        status=FusionRunStatus.SUCCEEDED,
        supporting_finding_ids=supporting,
        contradictory_finding_ids=contradictory,
        participating_modalities=participating,
        unavailable_modalities=unavailable,
        agreement=agreement,
        conflicts=conflicts,
        jury_assessments=jury_assessments,
        explanation=_build_explanation(verdict, agreement, conflicts),
        limitations=(
            "Fusion uses deterministic weighting; unavailable models are excluded."
        ),
        provenance={
            "evidence_id": str(evidence_id),
            "source_sha256": source_hash,
            "findings_count": len(findings),
            "policy_version": POLICY_VERSION,
        },
        engine_version=ENGINE_VERSION,
        policy_version=POLICY_VERSION,
    )
    return FusionResult(
        status=FusionRunStatus.SUCCEEDED,
        assessment=assessment,
        normalized_findings=findings,
        modality_statuses=modality_statuses,
        metadata={
            "findings_count": len(findings),
            "conflicts_count": len(conflicts),
            "jury_count": len(jury_assessments),
        },
    )


def _risk_score(findings: tuple[NormalizedFinding, ...]) -> float | None:
    actionable = [
        item
        for item in findings
        if item.verdict != FindingVerdict.UNAVAILABLE
    ]
    if not actionable:
        return None
    total = 0.0
    for finding in actionable:
        weight = _SEVERITY_WEIGHT.get(finding.severity, 0.1)
        if finding.confidence is not None:
            weight *= finding.confidence
        if finding.verdict in {
            FindingVerdict.SUPPORTS_SUSPICIOUS,
            FindingVerdict.SUPPORTS_FRAUD,
        }:
            total += weight
    max_score = len(actionable) * 1.0
    if max_score <= 0:
        return None
    return round(min(total / max_score, 1.0) * 100.0, 2)


def _fusion_confidence(
    findings: tuple[NormalizedFinding, ...],
    jury_assessments: tuple[JuryAssessment, ...],
    agreement: object,
) -> float | None:
    _ = agreement
    jury_confidences = [
        item.confidence
        for item in jury_assessments
        if item.confidence is not None
        and item.availability == ModalityAvailability.AVAILABLE
    ]
    finding_confidences = [
        item.confidence
        for item in findings
        if item.confidence is not None
        and item.verdict != FindingVerdict.UNAVAILABLE
    ]
    values = jury_confidences or finding_confidences
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _build_explanation(
    verdict: FusionVerdict,
    agreement: object,
    conflicts: tuple[FusionConflict, ...],
) -> str:
    conflict_note = (
        f" {len(conflicts)} cross-modal conflict(s) detected."
        if conflicts
        else ""
    )
    return (
        f"Final multimodal verdict: {verdict.value}.{conflict_note} "
        f"Jury agreement ratio: {getattr(agreement, 'jury_agreement_ratio', 0)}."
    )


def _insufficient_assessment(
    *,
    evidence_id: UUID,
    source_hash: str,
    findings: tuple[NormalizedFinding, ...],
    modality_statuses: tuple[ModalityStatus, ...],
    jury_assessments: tuple[JuryAssessment, ...],
    conflicts: tuple[FusionConflict, ...],
) -> FusionAssessment:
    agreement = compute_agreement(findings, modality_statuses, jury_assessments)
    return FusionAssessment(
        verdict=FusionVerdict.INSUFFICIENT_EVIDENCE,
        risk_score=None,
        confidence=None,
        status=FusionRunStatus.SUCCEEDED,
        supporting_finding_ids=(),
        contradictory_finding_ids=(),
        participating_modalities=(),
        unavailable_modalities=tuple(
            status.modality for status in modality_statuses
        ),
        agreement=agreement,
        conflicts=conflicts,
        jury_assessments=jury_assessments,
        explanation="No findings available for multimodal fusion.",
        limitations="Run modality analyses before fusion.",
        provenance={
            "evidence_id": str(evidence_id),
            "source_sha256": source_hash,
            "findings_count": 0,
            "policy_version": POLICY_VERSION,
        },
        engine_version=ENGINE_VERSION,
        policy_version=POLICY_VERSION,
    )
