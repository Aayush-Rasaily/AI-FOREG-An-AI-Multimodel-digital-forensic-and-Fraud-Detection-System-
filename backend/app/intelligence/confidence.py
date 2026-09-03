"""Deterministic confidence scoring for investigation summaries."""

from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> int:
    return int(round(max(low, min(high, value))))


def compute_overall_confidence(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Compute 0–100 overall confidence from stored analysis coverage."""

    evidence = list(snapshot.get("evidence", []))
    evidence_count = len(evidence)
    if evidence_count == 0:
        return {
            "overall_confidence": 0,
            "factors": {
                "coverage": 0.0,
                "agreement": 0.0,
                "analysis_completeness": 0.0,
                "finding_confidence": 0.0,
                "fusion_confidence": 0.0,
                "missing_analyses_penalty": 0.0,
            },
        }

    analyzed = sum(
        1
        for item in evidence
        if item.get("coverage_status") not in {None, "not_analyzed"}
    )
    coverage = analyzed / evidence_count

    fusion_rows = list(snapshot.get("fusion_snapshots", []))
    fusion_confidences = [
        float(item["confidence"])
        for item in fusion_rows
        if isinstance(item.get("confidence"), (int, float))
    ]
    fusion_confidence = (
        sum(fusion_confidences) / len(fusion_confidences)
        if fusion_confidences
        else 0.0
    )

    finding_scores: list[float] = []
    for summary in snapshot.get("analysis_summaries", []):
        for finding in summary.get("forensic_findings", []):
            if isinstance(finding.get("confidence"), (int, float)):
                finding_scores.append(float(finding["confidence"]))
    finding_confidence = (
        sum(finding_scores) / len(finding_scores) if finding_scores else 0.0
    )

    has_timeline = 1.0 if snapshot.get("timeline") else 0.0
    has_correlation = 1.0 if snapshot.get("correlation") else 0.0
    has_entities = 1.0 if snapshot.get("entity_resolution") else 0.0
    has_case_intel = 1.0 if snapshot.get("case_intelligence") else 0.0
    analysis_completeness = (
        coverage * 0.5
        + (len(fusion_rows) / evidence_count) * 0.2
        + has_timeline * 0.1
        + has_correlation * 0.1
        + has_entities * 0.05
        + has_case_intel * 0.05
    )

    verdicts = [
        str(item.get("verdict") or "")
        for item in fusion_rows
        if item.get("verdict")
    ]
    if len(verdicts) <= 1:
        agreement = 1.0 if verdicts else 0.0
    else:
        majority = max(verdicts.count(v) for v in set(verdicts))
        agreement = majority / len(verdicts)

    missing = evidence_count - analyzed
    missing_penalty = min(0.4, missing / max(evidence_count, 1) * 0.4)

    raw = (
        coverage * 25.0
        + agreement * 20.0
        + analysis_completeness * 20.0
        + finding_confidence * 15.0
        + fusion_confidence * 20.0
        - missing_penalty * 100.0
    )
    return {
        "overall_confidence": _clamp(raw),
        "factors": {
            "coverage": round(coverage, 4),
            "agreement": round(agreement, 4),
            "analysis_completeness": round(analysis_completeness, 4),
            "finding_confidence": round(finding_confidence, 4),
            "fusion_confidence": round(fusion_confidence, 4),
            "missing_analyses_penalty": round(missing_penalty, 4),
        },
    }
