"""Cross-modal conflict detection."""

from __future__ import annotations

from backend.app.forensics.models import Severity
from backend.app.fusion.models import (
    ConflictResolutionStatus,
    ConflictType,
    FindingVerdict,
    FusionConflict,
    JuryAssessment,
    Modality,
    NormalizedFinding,
)

_SUSPICIOUS = frozenset(
    {
        FindingVerdict.SUPPORTS_SUSPICIOUS,
        FindingVerdict.SUPPORTS_FRAUD,
    }
)


def detect_conflicts(
    findings: tuple[NormalizedFinding, ...],
    jury_assessments: tuple[JuryAssessment, ...],
) -> tuple[FusionConflict, ...]:
    """Identify structural conflicts without hiding disagreement."""

    conflicts: list[FusionConflict] = []
    conflicts.extend(_modality_verdict_conflicts(findings))
    conflicts.extend(_jury_verdict_conflicts(jury_assessments))
    conflicts.extend(_confidence_spread_conflicts(findings))
    return tuple(conflicts)


def _modality_verdict_conflicts(
    findings: tuple[NormalizedFinding, ...],
) -> list[FusionConflict]:
    by_modality: dict[Modality, list[NormalizedFinding]] = {}
    for finding in findings:
        if finding.verdict == FindingVerdict.UNAVAILABLE:
            continue
        by_modality.setdefault(finding.modality, []).append(finding)
    conflicts: list[FusionConflict] = []
    suspicious_modalities: set[Modality] = set()
    genuine_modalities: set[Modality] = set()
    for modality, items in by_modality.items():
        verdicts = {item.verdict for item in items}
        if verdicts & _SUSPICIOUS:
            suspicious_modalities.add(modality)
        if FindingVerdict.SUPPORTS_GENUINE in verdicts:
            genuine_modalities.add(modality)
    overlap = suspicious_modalities & genuine_modalities
    if overlap:
        involved = [
            item.finding_id
            for item in findings
            if item.modality in overlap
        ]
        conflicts.append(
            FusionConflict(
                conflict_id=(
                    "modality_disagreement:"
                    f"{','.join(sorted(m.value for m in overlap))}"
                ),
                conflict_type=ConflictType.MODALITY_DISAGREEMENT,
                severity=Severity.MEDIUM,
                involved_finding_ids=tuple(involved),
                involved_modalities=tuple(sorted(overlap, key=lambda m: m.value)),
                explanation=(
                    "Some modalities report suspicious indicators while others "
                    "report genuine-supporting signals."
                ),
            )
        )
    suspicious_only = suspicious_modalities - genuine_modalities
    genuine_only = genuine_modalities - suspicious_modalities
    if suspicious_only and genuine_only:
        involved = [
            item.finding_id
            for item in findings
            if item.modality in suspicious_only | genuine_only
        ]
        conflicts.append(
            FusionConflict(
                conflict_id=(
                    "verdict_disagreement:"
                    f"{','.join(sorted(m.value for m in suspicious_only))}"
                ),
                conflict_type=ConflictType.VERDICT_DISAGREEMENT,
                severity=Severity.HIGH,
                involved_finding_ids=tuple(involved),
                involved_modalities=tuple(
                    sorted(suspicious_only | genuine_only, key=lambda m: m.value)
                ),
                explanation=(
                    "Modalities disagree on suspicious versus genuine indicators."
                ),
            )
        )
    return conflicts


def _jury_verdict_conflicts(
    assessments: tuple[JuryAssessment, ...],
) -> list[FusionConflict]:
    available = [
        item
        for item in assessments
        if item.availability.value == "available"
    ]
    if len(available) < 2:
        return []
    verdicts = {item.verdict for item in available}
    if len(verdicts) <= 1:
        return []
    return [
        FusionConflict(
            conflict_id="jury_verdict_disagreement",
            conflict_type=ConflictType.VERDICT_DISAGREEMENT,
            severity=Severity.MEDIUM,
            involved_finding_ids=tuple(
                finding_id
                for assessment in available
                for finding_id in assessment.supporting_finding_ids
            ),
            involved_modalities=(),
            explanation="Jury members produced differing verdicts.",
        )
    ]


def _confidence_spread_conflicts(
    findings: tuple[NormalizedFinding, ...],
) -> list[FusionConflict]:
    values = [
        item.confidence
        for item in findings
        if item.confidence is not None
        and item.verdict != FindingVerdict.UNAVAILABLE
    ]
    if len(values) < 2:
        return []
    spread = max(values) - min(values)
    if spread < 0.5:
        return []
    high = [item for item in findings if item.confidence == max(values)]
    low = [item for item in findings if item.confidence == min(values)]
    involved = tuple(
        {item.finding_id for item in high + low}
    )
    return [
        FusionConflict(
            conflict_id="confidence_disagreement",
            conflict_type=ConflictType.CONFIDENCE_DISAGREEMENT,
            severity=Severity.LOW,
            involved_finding_ids=involved,
            involved_modalities=tuple(
                sorted({item.modality for item in high + low}, key=lambda m: m.value)
            ),
            explanation=(
                f"Confidence spread of {spread:.2f} across actionable findings."
            ),
            resolution_status=ConflictResolutionStatus.OPEN,
        )
    ]
