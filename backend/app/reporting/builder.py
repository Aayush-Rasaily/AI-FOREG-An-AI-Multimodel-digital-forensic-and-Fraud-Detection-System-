"""Build structured forensic report sections."""

from __future__ import annotations

from typing import Any

from backend.app.reporting.explainability import build_explainability
from backend.app.reporting.policy import ENGINE_VERSION, REPORT_VERSION


def _executive_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    case_intelligence = snapshot.get("case_intelligence") or {}
    coverage = case_intelligence.get("coverage") or {}
    evidence = snapshot.get("evidence") or []
    explainability = build_explainability(snapshot)
    return {
        "case_verdict": case_intelligence.get("verdict"),
        "risk_score": case_intelligence.get("risk_score"),
        "confidence": case_intelligence.get("confidence"),
        "evidence_count": len(evidence),
        "analyzed_evidence": coverage.get("analyzed", 0),
        "unavailable_evidence": coverage.get("unavailable", 0),
        "inconclusive_evidence": coverage.get("inconclusive", 0),
        "not_analyzed_evidence": coverage.get("not_analyzed", 0),
        "major_supporting_findings": explainability["supporting_findings"][:10],
        "major_contradictions": explainability["contradictory_findings"][:10],
        "open_conflicts": len(explainability["conflicts"]),
        "limitations": explainability["limitations"][:10],
    }


def build_report_content(
    *,
    report_id: str,
    generated_at: str,
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Build the full structured report from an aggregated snapshot."""

    case = snapshot["case"]
    explainability = build_explainability(snapshot)
    case_intelligence = snapshot.get("case_intelligence")

    sections: dict[str, Any] = {
        "case_information": case,
        "executive_summary": _executive_summary(snapshot),
        "evidence_inventory": snapshot.get("evidence", []),
        "evidence_integrity": [
            {
                "evidence_id": item["evidence_id"],
                "evidence_number": item["evidence_number"],
                "sha256_hash": item["sha256_hash"],
                "custody_event_count": len(item.get("custody_events", [])),
                "ingested_at": item.get("ingested_at"),
                "verification_note": (
                    "Hash recorded at ingestion; re-verification not performed "
                    "during report generation."
                ),
            }
            for item in snapshot.get("evidence", [])
        ],
        "evidence_processing": [
            {
                "evidence_id": item["evidence_id"],
                "evidence_number": item["evidence_number"],
                "processing_status": item.get("processing_status"),
                "status": item.get("status"),
            }
            for item in snapshot.get("evidence", [])
        ],
        "modality_analysis": snapshot.get("analysis_summaries", []),
        "multimodal_jury_assessment": snapshot.get("fusion_snapshots", []),
        "explainability": explainability,
    }

    if case_intelligence:
        sections["case_level_intelligence"] = case_intelligence
        sections["cross_evidence_relationships"] = case_intelligence.get(
            "relationships",
            [],
        )
        sections["conflicts_and_contradictions"] = case_intelligence.get(
            "conflicts",
            [],
        )
        sections["investigation_timeline"] = case_intelligence.get("timeline", [])
        sections["risk_assessment"] = {
            "case_risk_score": case_intelligence.get("risk_score"),
            "case_confidence": case_intelligence.get("confidence"),
            "case_verdict": case_intelligence.get("verdict"),
            "note": explainability["confidence_note"],
        }
        sections["final_assessment"] = {
            "case_verdict": case_intelligence.get("verdict"),
            "risk_score": case_intelligence.get("risk_score"),
            "confidence": case_intelligence.get("confidence"),
            "distinction": (
                "Case-level conclusions aggregate evidence-level fusion results."
            ),
        }

    sections["confidence_and_limitations"] = {
        "limitations": explainability["limitations"],
        "uncertainties": explainability["uncertainties"],
        "confidence_note": explainability["confidence_note"],
        "jury_note": explainability["jury_note"],
    }
    sections["provenance_chain_of_custody"] = {
        "case_id": case["case_id"],
        "evidence_hashes": snapshot.get("evidence_hashes", []),
        "case_intelligence_run_id": (
            case_intelligence.get("analysis_run_id") if case_intelligence else None
        ),
        "fusion_run_ids": [
            item["fusion_run_id"] for item in snapshot.get("fusion_snapshots", [])
        ],
    }
    sections["technical_appendix"] = {
        "report_version": REPORT_VERSION,
        "engine_version": ENGINE_VERSION,
        "fusion_policy_versions": sorted(
            {
                item["policy_version"]
                for item in snapshot.get("fusion_snapshots", [])
                if item.get("policy_version")
            }
        ),
        "case_intelligence_policy_version": (
            case_intelligence.get("policy_version") if case_intelligence else None
        ),
    }

    return {
        "report_id": report_id,
        "report_version": REPORT_VERSION,
        "engine_version": ENGINE_VERSION,
        "generated_at": generated_at,
        "title": f"Forensic Investigation Report — {case['case_number']}",
        "sections": sections,
    }
