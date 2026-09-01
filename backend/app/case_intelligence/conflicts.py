"""Case-level conflict detection."""

from __future__ import annotations

from backend.app.case_intelligence.models import (
    CaseConflict,
    CaseConflictType,
    ConflictResolutionStatus,
    EvidenceParticipation,
)
from backend.app.forensics.models import Severity
from backend.app.fusion.models import FusionVerdict

_SUSPICIOUS = frozenset({FusionVerdict.SUSPICIOUS, FusionVerdict.POTENTIAL_FRAUD})
_GENUINE = frozenset({FusionVerdict.GENUINE})


def detect_case_conflicts(
    participations: tuple[EvidenceParticipation, ...],
    consistency_conflicts: tuple[CaseConflict, ...],
) -> tuple[CaseConflict, ...]:
    """Preserve cross-evidence disagreement at case level."""

    conflicts = list(consistency_conflicts)
    suspicious_ids = [
        item.evidence_id
        for item in participations
        if item.fusion_verdict in _SUSPICIOUS
    ]
    genuine_ids = [
        item.evidence_id
        for item in participations
        if item.fusion_verdict in _GENUINE
    ]
    if suspicious_ids and genuine_ids:
        conflicts.append(
            CaseConflict(
                conflict_id=(
                    "verdict_disagreement:"
                    f"{','.join(str(value) for value in sorted(suspicious_ids))}"
                ),
                involved_evidence_ids=tuple(sorted(suspicious_ids + genuine_ids)),
                involved_finding_ids=tuple(
                    finding_id
                    for item in participations
                    for finding_id in item.supporting_finding_ids
                ),
                conflict_type=CaseConflictType.VERDICT_DISAGREEMENT,
                severity=Severity.HIGH,
                explanation=(
                    "Evidence items disagree between suspicious and "
                    "genuine fusion verdicts."
                ),
                resolution_status=ConflictResolutionStatus.OPEN,
            )
        )
    confidence_values = [
        (item.evidence_id, item.confidence)
        for item in participations
        if item.confidence is not None
    ]
    if len(confidence_values) >= 2:
        spread = max(value for _, value in confidence_values) - min(
            value for _, value in confidence_values
        )
        if spread >= 0.4:
            conflicts.append(
                CaseConflict(
                    conflict_id="confidence_disagreement:case",
                    involved_evidence_ids=tuple(
                        evidence_id for evidence_id, _ in confidence_values
                    ),
                    involved_finding_ids=(),
                    conflict_type=CaseConflictType.CONFIDENCE_DISAGREEMENT,
                    severity=Severity.MEDIUM,
                    explanation=(
                        "Evidence-level fusion confidence values diverge significantly."
                    ),
                    resolution_status=ConflictResolutionStatus.OPEN,
                )
            )
    for item in participations:
        if item.contradictory_finding_ids and item.fusion_verdict in _SUSPICIOUS:
            conflicts.append(
                CaseConflict(
                    conflict_id=f"forensic_contradiction:{item.evidence_id}",
                    involved_evidence_ids=(item.evidence_id,),
                    involved_finding_ids=item.contradictory_finding_ids,
                    conflict_type=CaseConflictType.FORENSIC_CONTRADICTION,
                    severity=Severity.MEDIUM,
                    explanation=(
                        "Evidence contains contradictory findings alongside "
                        "suspicious verdict."
                    ),
                    resolution_status=ConflictResolutionStatus.OPEN,
                )
            )
    return _deduplicate_conflicts(conflicts)


def _deduplicate_conflicts(conflicts: list[CaseConflict]) -> tuple[CaseConflict, ...]:
    seen: set[str] = set()
    unique: list[CaseConflict] = []
    for item in sorted(conflicts, key=lambda row: row.conflict_id):
        if item.conflict_id in seen:
            continue
        seen.add(item.conflict_id)
        unique.append(item)
    return tuple(unique)
