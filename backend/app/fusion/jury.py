"""Deterministic AI jury assessments."""

from __future__ import annotations

from backend.app.fusion.models import (
    FindingVerdict,
    FusionVerdict,
    JuryAssessment,
    JuryMemberRole,
    Modality,
    ModalityAvailability,
    NormalizedFinding,
)

_ROLE_LABELS = {
    JuryMemberRole.FORENSIC_ANALYST: "Forensic Evidence Analyst",
    JuryMemberRole.DOCUMENT_IMAGE_SPECIALIST: "Document / Image Specialist",
    JuryMemberRole.MULTIMEDIA_SPECIALIST: "Multimedia Specialist",
    JuryMemberRole.SIGNATURE_SPECIALIST: "Signature Specialist",
    JuryMemberRole.CONSISTENCY_ANALYST: "Consistency Analyst",
    JuryMemberRole.SENIOR_JUDGE: "Senior Forensic Judge",
}

_SUSPICIOUS_VERDICTS = frozenset(
    {
        FindingVerdict.SUPPORTS_SUSPICIOUS,
        FindingVerdict.SUPPORTS_FRAUD,
    }
)
_GENUINE_VERDICTS = frozenset({FindingVerdict.SUPPORTS_GENUINE})


def assess_jury(
    findings: tuple[NormalizedFinding, ...],
) -> tuple[JuryAssessment, ...]:
    """Produce deterministic jury assessments from normalized findings."""

    member_findings = {
        JuryMemberRole.FORENSIC_ANALYST: _filter_modalities(
            findings,
            {Modality.FORENSICS, Modality.COMPARISON},
        ),
        JuryMemberRole.DOCUMENT_IMAGE_SPECIALIST: _filter_modalities(
            findings,
            {Modality.DOCUMENT_AI, Modality.IMAGE_AI},
        ),
        JuryMemberRole.MULTIMEDIA_SPECIALIST: _filter_modalities(
            findings,
            {Modality.VIDEO_AI, Modality.AUDIO_AI},
        ),
        JuryMemberRole.SIGNATURE_SPECIALIST: _filter_modalities(
            findings,
            {Modality.SIGNATURE_AI},
        ),
        JuryMemberRole.CONSISTENCY_ANALYST: findings,
    }
    assessments: list[JuryAssessment] = []
    for role, scoped in member_findings.items():
        if role != JuryMemberRole.CONSISTENCY_ANALYST:
            assessments.append(_assess_role(role, scoped))
    specialist_assessments = tuple(assessments)
    assessments.append(
        _assess_senior_judge(specialist_assessments, member_findings)
    )
    return tuple(assessments)


def _filter_modalities(
    findings: tuple[NormalizedFinding, ...],
    modalities: set[Modality],
) -> tuple[NormalizedFinding, ...]:
    return tuple(item for item in findings if item.modality in modalities)


def _assess_role(
    role: JuryMemberRole,
    findings: tuple[NormalizedFinding, ...],
) -> JuryAssessment:
    actionable = [
        item
        for item in findings
        if item.verdict != FindingVerdict.UNAVAILABLE
    ]
    if not findings:
        return JuryAssessment(
            role=role,
            member_name=_ROLE_LABELS[role],
            verdict=FusionVerdict.INSUFFICIENT_EVIDENCE,
            confidence=None,
            availability=ModalityAvailability.INSUFFICIENT_EVIDENCE,
            supporting_finding_ids=(),
            contradictory_finding_ids=(),
            explanation="No findings available for this jury member scope.",
            limitations="Insufficient modality evidence.",
        )
    if not actionable:
        return JuryAssessment(
            role=role,
            member_name=_ROLE_LABELS[role],
            verdict=FusionVerdict.UNAVAILABLE,
            confidence=None,
            availability=ModalityAvailability.UNAVAILABLE,
            supporting_finding_ids=(),
            contradictory_finding_ids=tuple(
                item.finding_id for item in findings
            ),
            explanation="Scoped findings are unavailable capability states only.",
            limitations="Unavailable analysis is not treated as negative evidence.",
        )
    supporting = [
        item.finding_id
        for item in actionable
        if item.verdict in _SUSPICIOUS_VERDICTS
    ]
    genuine = [
        item.finding_id
        for item in actionable
        if item.verdict in _GENUINE_VERDICTS
    ]
    fraud_count = sum(
        1 for item in actionable if item.verdict == FindingVerdict.SUPPORTS_FRAUD
    )
    suspicious_count = sum(
        1
        for item in actionable
        if item.verdict == FindingVerdict.SUPPORTS_SUSPICIOUS
    )
    if fraud_count > 0:
        verdict = FusionVerdict.POTENTIAL_FRAUD
    elif suspicious_count > 0:
        verdict = FusionVerdict.SUSPICIOUS
    elif genuine and not supporting:
        verdict = FusionVerdict.GENUINE
    elif supporting and genuine:
        verdict = FusionVerdict.INCONCLUSIVE
    else:
        verdict = FusionVerdict.INCONCLUSIVE
    confidences = [
        item.confidence for item in actionable if item.confidence is not None
    ]
    confidence = (
        round(sum(confidences) / len(confidences), 4) if confidences else None
    )
    return JuryAssessment(
        role=role,
        member_name=_ROLE_LABELS[role],
        verdict=verdict,
        confidence=confidence,
        availability=ModalityAvailability.AVAILABLE,
        supporting_finding_ids=tuple(supporting),
        contradictory_finding_ids=tuple(genuine),
        explanation=(
            f"Reviewed {len(actionable)} actionable findings in scope. "
            f"Suspicious indicators: {len(supporting)}."
        ),
        limitations=(
            "Deterministic rule-based assessment; not a validated identity model."
        ),
    )


def _assess_senior_judge(
    specialists: tuple[JuryAssessment, ...],
    scoped: dict[JuryMemberRole, tuple[NormalizedFinding, ...]],
) -> JuryAssessment:
    available = [
        item
        for item in specialists
        if item.availability == ModalityAvailability.AVAILABLE
    ]
    if not available:
        return JuryAssessment(
            role=JuryMemberRole.SENIOR_JUDGE,
            member_name=_ROLE_LABELS[JuryMemberRole.SENIOR_JUDGE],
            verdict=FusionVerdict.INSUFFICIENT_EVIDENCE,
            confidence=None,
            availability=ModalityAvailability.INSUFFICIENT_EVIDENCE,
            supporting_finding_ids=(),
            contradictory_finding_ids=(),
            explanation="No specialist jury assessments were available.",
            limitations="Cannot aggregate without specialist input.",
        )
    fraud_votes = sum(
        1 for item in available if item.verdict == FusionVerdict.POTENTIAL_FRAUD
    )
    suspicious_votes = sum(
        1 for item in available if item.verdict == FusionVerdict.SUSPICIOUS
    )
    genuine_votes = sum(
        1 for item in available if item.verdict == FusionVerdict.GENUINE
    )
    if fraud_votes >= 2:
        verdict = FusionVerdict.POTENTIAL_FRAUD
    elif fraud_votes == 1 or suspicious_votes >= 2:
        verdict = FusionVerdict.SUSPICIOUS
    elif genuine_votes >= 2 and fraud_votes == 0 and suspicious_votes == 0:
        verdict = FusionVerdict.GENUINE
    else:
        verdict = FusionVerdict.INCONCLUSIVE
    confidences = [item.confidence for item in available if item.confidence is not None]
    confidence = (
        round(sum(confidences) / len(confidences), 4) if confidences else None
    )
    supporting = tuple(
        finding_id
        for assessment in available
        for finding_id in assessment.supporting_finding_ids
    )
    contradictory = tuple(
        finding_id
        for assessment in available
        for finding_id in assessment.contradictory_finding_ids
    )
    _ = scoped
    return JuryAssessment(
        role=JuryMemberRole.SENIOR_JUDGE,
        member_name=_ROLE_LABELS[JuryMemberRole.SENIOR_JUDGE],
        verdict=verdict,
        confidence=confidence,
        availability=ModalityAvailability.AVAILABLE,
        supporting_finding_ids=supporting,
        contradictory_finding_ids=contradictory,
        explanation=(
            f"Aggregated {len(available)} specialist assessments. "
            f"Fraud votes: {fraud_votes}, suspicious: {suspicious_votes}."
        ),
        limitations="Senior judge uses deterministic vote aggregation only.",
        model_name="fusion_jury",
        model_version="1.0.0",
    )
