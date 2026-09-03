"""Key finding extraction and risk scoring from stored outputs."""

from __future__ import annotations

from typing import Any

from backend.app.intelligence.models import CaseRiskLevel
from backend.app.intelligence.provenance import provenance

_SEVERITY_RANK = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1,
    "informational": 1,
}

_VERDICT_RISK = {
    "potential_fraud": 90,
    "suspicious": 70,
    "inconclusive": 40,
    "genuine": 10,
}


def _severity_rank(value: str | None) -> int:
    if not value:
        return 0
    return _SEVERITY_RANK.get(str(value).lower(), 0)


def extract_key_findings(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify highest-severity and most relevant stored findings."""

    items: list[dict[str, Any]] = []
    for summary in snapshot.get("analysis_summaries", []):
        evidence_id = str(summary.get("evidence_id") or "")
        for finding in summary.get("forensic_findings", []):
            severity = str(finding.get("severity") or "info").lower()
            items.append(
                {
                    "title": str(finding.get("category") or "finding"),
                    "severity": severity,
                    "confidence": finding.get("confidence"),
                    "summary": str(
                        finding.get("description")
                        or finding.get("explanation")
                        or "Stored forensic finding."
                    ),
                    "provenance": provenance(
                        evidence_ids=[evidence_id] if evidence_id else [],
                        finding_ids=[str(finding.get("finding_id") or "")],
                    ),
                    "_rank": _severity_rank(severity),
                }
            )

    for fusion in snapshot.get("fusion_snapshots", []):
        verdict = str(fusion.get("verdict") or "unknown")
        evidence_id = str(fusion.get("evidence_id") or "")
        fusion_id = str(fusion.get("fusion_run_id") or "")
        risk = fusion.get("risk_score")
        severity = "high"
        if isinstance(risk, (int, float)):
            if risk >= 80:
                severity = "critical"
            elif risk >= 60:
                severity = "high"
            elif risk >= 30:
                severity = "medium"
            else:
                severity = "low"
        items.append(
            {
                "title": f"fusion:{verdict}",
                "severity": severity,
                "confidence": fusion.get("confidence"),
                "summary": (
                    f"Fusion verdict '{verdict}' for evidence "
                    f"{fusion.get('evidence_number') or evidence_id}."
                ),
                "provenance": provenance(
                    evidence_ids=[evidence_id] if evidence_id else [],
                    fusion_ids=[fusion_id] if fusion_id else [],
                ),
                "_rank": _severity_rank(severity),
            }
        )

    not_analyzed = [
        item
        for item in snapshot.get("evidence", [])
        if item.get("coverage_status") in {None, "not_analyzed"}
    ]
    if not_analyzed:
        ids = [str(item["evidence_id"]) for item in not_analyzed]
        items.append(
            {
                "title": "unavailable_analyses",
                "severity": "medium",
                "confidence": None,
                "summary": (
                    f"{len(not_analyzed)} evidence item(s) lack fusion "
                    "or coverage analysis."
                ),
                "provenance": provenance(evidence_ids=ids),
                "_rank": _severity_rank("medium"),
            }
        )

    items.sort(
        key=lambda row: (
            -int(row["_rank"]),
            -(
                float(row["confidence"])
                if isinstance(row.get("confidence"), (int, float))
                else -1.0
            ),
            str(row["title"]),
            str(row["summary"]),
        )
    )
    for row in items:
        row.pop("_rank", None)
    return items[:25]


def compute_overall_risk(
    snapshot: dict[str, Any],
    key_findings: list[dict[str, Any]],
) -> CaseRiskLevel:
    """Derive overall case risk from fusion scores and finding severity."""

    scores: list[float] = []
    for fusion in snapshot.get("fusion_snapshots", []):
        if isinstance(fusion.get("risk_score"), (int, float)):
            scores.append(float(fusion["risk_score"]))
        else:
            verdict = str(fusion.get("verdict") or "")
            scores.append(float(_VERDICT_RISK.get(verdict, 30)))

    case_intel = snapshot.get("case_intelligence") or {}
    if isinstance(case_intel.get("risk_score"), (int, float)):
        scores.append(float(case_intel["risk_score"]))

    max_finding = max(
        (_severity_rank(str(item.get("severity"))) for item in key_findings),
        default=0,
    )
    if max_finding >= 5:
        scores.append(95.0)
    elif max_finding >= 4:
        scores.append(75.0)
    elif max_finding >= 3:
        scores.append(50.0)

    if not scores:
        evidence_count = len(snapshot.get("evidence", []))
        return CaseRiskLevel.LOW if evidence_count == 0 else CaseRiskLevel.MEDIUM

    peak = max(scores)
    if peak >= 85:
        return CaseRiskLevel.CRITICAL
    if peak >= 65:
        return CaseRiskLevel.HIGH
    if peak >= 35:
        return CaseRiskLevel.MEDIUM
    return CaseRiskLevel.LOW
