"""Deterministic agreement analysis."""

from __future__ import annotations

from backend.app.fusion.models import (
    AgreementMetrics,
    FindingVerdict,
    JuryAssessment,
    Modality,
    ModalityAvailability,
    ModalityStatus,
    NormalizedFinding,
)

_SUSPICIOUS = frozenset(
    {
        FindingVerdict.SUPPORTS_SUSPICIOUS,
        FindingVerdict.SUPPORTS_FRAUD,
    }
)


def compute_agreement(
    findings: tuple[NormalizedFinding, ...],
    modality_statuses: tuple[ModalityStatus, ...],
    jury_assessments: tuple[JuryAssessment, ...],
) -> AgreementMetrics:
    """Calculate auditable agreement metrics."""

    actionable = [
        item
        for item in findings
        if item.verdict != FindingVerdict.UNAVAILABLE
    ]
    supporting_modalities: set[Modality] = set()
    contradictory_modalities: set[Modality] = set()
    for finding in actionable:
        if finding.verdict in _SUSPICIOUS:
            supporting_modalities.add(finding.modality)
        elif finding.verdict == FindingVerdict.SUPPORTS_GENUINE:
            contradictory_modalities.add(finding.modality)
    overlap = supporting_modalities & contradictory_modalities
    supporting_modalities -= overlap
    contradictory_modalities -= overlap
    unavailable_modalities = sum(
        1
        for status in modality_statuses
        if status.availability
        in {
            ModalityAvailability.UNAVAILABLE,
            ModalityAvailability.FAILED,
        }
    )
    inconclusive_modalities = sum(
        1
        for status in modality_statuses
        if status.availability == ModalityAvailability.INSUFFICIENT_EVIDENCE
    )
    participating = len(supporting_modalities) + len(contradictory_modalities)
    modality_agreement = (
        len(supporting_modalities) / participating if participating else 0.0
    )
    available_jury = [
        item
        for item in jury_assessments
        if item.availability == ModalityAvailability.AVAILABLE
    ]
    if not available_jury:
        jury_agreement = 0.0
    else:
        verdicts = [item.verdict for item in available_jury]
        majority = max(set(verdicts), key=verdicts.count)
        jury_agreement = verdicts.count(majority) / len(verdicts)
    confidences = [
        item.confidence for item in actionable if item.confidence is not None
    ]
    spread = (max(confidences) - min(confidences)) if len(confidences) >= 2 else None
    return AgreementMetrics(
        modality_agreement_ratio=round(modality_agreement, 4),
        jury_agreement_ratio=round(jury_agreement, 4),
        supporting_modalities=len(supporting_modalities),
        contradictory_modalities=len(contradictory_modalities),
        unavailable_modalities=unavailable_modalities,
        inconclusive_modalities=inconclusive_modalities,
        confidence_spread=round(spread, 4) if spread is not None else None,
        jury_votes_available=len(available_jury),
        jury_votes_total=len(jury_assessments),
    )
