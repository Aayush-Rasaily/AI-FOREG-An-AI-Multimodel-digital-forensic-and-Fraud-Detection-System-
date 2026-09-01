"""Structured explainability for forensic reports."""

from __future__ import annotations

from typing import Any


def build_explainability(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Derive structured explanations from aggregated report data."""

    case_intelligence = snapshot.get("case_intelligence") or {}
    coverage = case_intelligence.get("coverage") or {}
    fusion_snapshots = snapshot.get("fusion_snapshots") or []
    evidence = snapshot.get("evidence") or []

    supporting_findings: list[str] = []
    for fusion in fusion_snapshots:
        supporting_findings.extend(fusion.get("supporting_finding_ids") or [])

    contradictory_findings: list[str] = []
    for fusion in fusion_snapshots:
        contradictory_findings.extend(fusion.get("contradictory_finding_ids") or [])

    limitations: list[str] = []
    if not case_intelligence:
        limitations.append("No Phase 6G case intelligence synthesis is available.")
    if case_intelligence.get("limitations"):
        limitations.append(str(case_intelligence["limitations"]))
    for item in evidence:
        if item.get("coverage_status") == "not_analyzed":
            limitations.append(
                f"Evidence {item['evidence_number']} has not been analyzed."
            )
        elif item.get("coverage_status") == "unavailable":
            limitations.append(
                f"Evidence {item['evidence_number']} analysis is unavailable."
            )
        elif item.get("coverage_status") == "inconclusive":
            limitations.append(
                f"Evidence {item['evidence_number']} analysis is inconclusive."
            )

    conflicts = case_intelligence.get("conflicts") or []
    for fusion in fusion_snapshots:
        for conflict in fusion.get("conflicts") or []:
            if conflict.get("resolution_status") == "open":
                conflicts.append(
                    {
                        "conflict_id": conflict["conflict_id"],
                        "conflict_type": conflict["conflict_type"],
                        "severity": conflict["severity"],
                        "explanation": conflict["explanation"],
                        "source": "fusion",
                    }
                )

    return {
        "why": case_intelligence.get("explanation")
        or "Case-level synthesis is not available; evidence-level results are listed.",
        "supporting_findings": sorted(set(supporting_findings)),
        "contradictory_findings": sorted(set(contradictory_findings)),
        "supporting_evidence_ids": case_intelligence.get("supporting_evidence_ids", []),
        "contradictory_evidence_ids": case_intelligence.get(
            "contradictory_evidence_ids",
            [],
        ),
        "conflicts": conflicts,
        "uncertainties": [
            item
            for item in evidence
            if item.get("coverage_status")
            in {"not_analyzed", "unavailable", "inconclusive", "insufficient_evidence"}
        ],
        "limitations": sorted(set(limitations)),
        "confidence_note": (
            "Risk score and confidence are separate metrics. "
            "Risk reflects assessed threat level; confidence reflects "
            "analytical certainty where available."
        ),
        "jury_note": (
            "Jury assessments are AI/system-generated deterministic evaluations, "
            "not live human expert opinions."
        ),
        "coverage": coverage,
    }
