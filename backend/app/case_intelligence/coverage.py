"""Case-level evidence coverage calculations."""

from __future__ import annotations

from backend.app.case_intelligence.models import (
    EvidenceCoverage,
    EvidenceCoverageStatus,
    EvidenceParticipation,
)
from backend.app.fusion.models import FusionVerdict

_SUSPICIOUS_VERDICTS = frozenset(
    {FusionVerdict.SUSPICIOUS, FusionVerdict.POTENTIAL_FRAUD}
)
_GENUINE_VERDICTS = frozenset({FusionVerdict.GENUINE})


def compute_coverage(
    participations: tuple[EvidenceParticipation, ...],
    *,
    open_conflicts: int,
) -> EvidenceCoverage:
    """Summarize evidence coverage for one case."""

    analyzed = sum(
        1
        for item in participations
        if item.coverage_status == EvidenceCoverageStatus.ANALYZED
    )
    not_analyzed = sum(
        1
        for item in participations
        if item.coverage_status == EvidenceCoverageStatus.NOT_ANALYZED
    )
    inconclusive = sum(
        1
        for item in participations
        if item.coverage_status == EvidenceCoverageStatus.INCONCLUSIVE
    )
    insufficient = sum(
        1
        for item in participations
        if item.coverage_status == EvidenceCoverageStatus.INSUFFICIENT_EVIDENCE
    )
    unavailable = sum(
        1
        for item in participations
        if item.coverage_status == EvidenceCoverageStatus.UNAVAILABLE
    )
    failed = sum(
        1
        for item in participations
        if item.coverage_status == EvidenceCoverageStatus.FAILED
    )
    supporting = sum(
        1
        for item in participations
        if item.fusion_verdict in _SUSPICIOUS_VERDICTS
    )
    contradictory = sum(
        1
        for item in participations
        if item.fusion_verdict in _GENUINE_VERDICTS
    )
    modalities: set[str] = set()
    for item in participations:
        modalities.update(item.participating_modalities)
    return EvidenceCoverage(
        total_evidence=len(participations),
        analyzed=analyzed,
        not_analyzed=not_analyzed,
        inconclusive=inconclusive,
        insufficient_evidence=insufficient,
        unavailable=unavailable,
        failed=failed,
        supporting_evidence=supporting,
        contradictory_evidence=contradictory,
        open_conflicts=open_conflicts,
        supported_modalities=tuple(sorted(modalities)),
    )
