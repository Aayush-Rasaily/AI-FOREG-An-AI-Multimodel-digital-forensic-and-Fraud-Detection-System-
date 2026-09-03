"""Build structured forensic report sections."""

from __future__ import annotations

from typing import Any

from backend.app.reporting.explainability import build_explainability
from backend.app.reporting.policy import ENGINE_VERSION, REPORT_VERSION
from backend.app.reporting.provenance import (
    SECTION_ORDER,
    content_checksum,
)


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
        "major_supporting_findings": (
            explainability["supporting_findings"][:10]
        ),
        "major_contradictions": (
            explainability["contradictory_findings"][:10]
        ),
        "open_conflicts": len(explainability["conflicts"]),
        "limitations": explainability["limitations"][:10],
    }


def _section_or_unavailable(
    data: Any,
    note: str,
) -> dict[str, Any]:
    if data is None:
        return {"available": False, "note": note}
    if isinstance(data, dict):
        return {"available": True, **data}
    if isinstance(data, list):
        return {"available": True, "count": len(data), "items": data}
    return {"available": True, "value": data}


def _build_metadata_summary(
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    items = []
    for ev in evidence:
        items.append({
            "evidence_id": ev["evidence_id"],
            "evidence_number": ev["evidence_number"],
            "mime_type": ev.get("mime_type"),
            "file_size": ev.get("file_size"),
            "sha256_hash": ev.get("sha256_hash"),
            "ingested_at": ev.get("ingested_at"),
        })
    return {"count": len(items), "items": items}


def _build_ocr_summary(
    summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    items = []
    for s in summaries:
        processing = s.get("processing_status")
        items.append({
            "evidence_id": s["evidence_id"],
            "evidence_number": s["evidence_number"],
            "processing_status": processing,
            "has_text_extraction": processing is not None,
        })
    return {"count": len(items), "items": items}


def _build_pattern_summary(
    summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    items = []
    for s in summaries:
        findings = s.get("forensic_findings", [])
        items.append({
            "evidence_id": s["evidence_id"],
            "evidence_number": s["evidence_number"],
            "pattern_count": len(findings),
        })
    return {"count": len(items), "items": items}


def _build_modality_section(
    summaries: list[dict[str, Any]],
    key: str,
    label: str,
) -> dict[str, Any]:
    items = []
    for s in summaries:
        value = s.get(key)
        if value is not None:
            items.append({
                "evidence_id": s["evidence_id"],
                "evidence_number": s["evidence_number"],
                "data": value,
            })
    if not items:
        return {
            "available": False,
            "note": f"{label} analysis not available.",
        }
    return {"available": True, "count": len(items), "items": items}


def _build_comparison_section(
    summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    items = []
    for s in summaries:
        value = s.get("comparison")
        if value is not None:
            items.append({
                "evidence_id": s["evidence_id"],
                "evidence_number": s["evidence_number"],
                "data": value,
            })
    if not items:
        return {
            "available": False,
            "note": "Evidence comparison analysis not available.",
        }
    return {"available": True, "count": len(items), "items": items}


def _collect_analysis_run_ids(
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    ids: dict[str, Any] = {}
    ci = snapshot.get("case_intelligence")
    if ci:
        ids["case_intelligence_run_id"] = ci.get("analysis_run_id")
    ids["fusion_run_ids"] = [
        item["fusion_run_id"]
        for item in snapshot.get("fusion_snapshots", [])
    ]
    corr = snapshot.get("correlation")
    if corr:
        ids["correlation_run_id"] = corr.get("run_id")
    ent = snapshot.get("entity_resolution")
    if ent:
        ids["entity_resolution_run_id"] = ent.get("run_id")
    tl = snapshot.get("timeline")
    if tl:
        ids["timeline_run_id"] = tl.get("run_id")
    return ids


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
    evidence = snapshot.get("evidence", [])
    summaries = snapshot.get("analysis_summaries", [])
    correlation = snapshot.get("correlation")
    entity_resolution = snapshot.get("entity_resolution")
    timeline = snapshot.get("timeline")

    sections: dict[str, Any] = {}

    # 1. case_summary
    sections["case_summary"] = {
        "available": True,
        **case,
        "executive_summary": _executive_summary(snapshot),
    }

    # 2. evidence_inventory
    sections["evidence_inventory"] = {
        "available": True,
        "count": len(evidence),
        "items": evidence,
    }

    # 3. metadata_summary
    sections["metadata_summary"] = _build_metadata_summary(evidence)

    # 4. ocr_summary
    sections["ocr_summary"] = _build_ocr_summary(summaries)

    # 5. pattern_extraction_summary
    sections["pattern_extraction_summary"] = (
        _build_pattern_summary(summaries)
    )

    # 6. timeline
    sections["timeline"] = _section_or_unavailable(
        timeline,
        "Investigation timeline not available.",
    )

    # 7. forensic_findings
    all_findings: list[dict[str, Any]] = []
    for s in summaries:
        for f in s.get("forensic_findings", []):
            all_findings.append({
                "evidence_id": s["evidence_id"],
                "evidence_number": s["evidence_number"],
                **f,
            })
    sections["forensic_findings"] = {
        "available": bool(all_findings),
        "count": len(all_findings),
        "items": all_findings,
    }

    # 8. evidence_comparison
    sections["evidence_comparison"] = (
        _build_comparison_section(summaries)
    )

    # 9-13. AI modality sections
    sections["image_ai"] = _build_modality_section(
        summaries, "image_ai", "Image AI",
    )
    sections["document_ai"] = _build_modality_section(
        summaries, "document_ai", "Document AI",
    )
    sections["signature_ai"] = _build_modality_section(
        summaries, "signature_ai", "Signature AI",
    )
    sections["video_ai"] = _build_modality_section(
        summaries, "video_ai", "Video AI",
    )
    sections["audio_ai"] = _build_modality_section(
        summaries, "audio_ai", "Audio AI",
    )

    # 14. fusion_assessment
    fusion_data = snapshot.get("fusion_snapshots", [])
    sections["fusion_assessment"] = {
        "available": bool(fusion_data),
        "count": len(fusion_data),
        "items": fusion_data,
    }

    # 15. correlation_summary
    sections["correlation_summary"] = _section_or_unavailable(
        correlation,
        "Cross-evidence correlation analysis not available.",
    )

    # 16. entity_graph_summary
    sections["entity_graph_summary"] = _section_or_unavailable(
        entity_resolution,
        "Entity resolution analysis not available.",
    )

    # 17. overall_confidence
    sections["overall_confidence"] = {
        "confidence_note": explainability["confidence_note"],
        "jury_note": explainability["jury_note"],
        "case_confidence": (
            case_intelligence.get("confidence")
            if case_intelligence
            else None
        ),
    }

    # 18. risk_assessment
    sections["risk_assessment"] = {
        "case_risk_score": (
            case_intelligence.get("risk_score")
            if case_intelligence
            else None
        ),
        "case_confidence": (
            case_intelligence.get("confidence")
            if case_intelligence
            else None
        ),
        "case_verdict": (
            case_intelligence.get("verdict")
            if case_intelligence
            else None
        ),
        "note": explainability["confidence_note"],
    }

    # 19. conflicts
    sections["conflicts"] = {
        "available": bool(explainability["conflicts"]),
        "count": len(explainability["conflicts"]),
        "items": explainability["conflicts"],
    }

    # 20. provenance_summary
    included = _collect_analysis_run_ids(snapshot)
    sections["provenance_summary"] = {
        "case_id": case["case_id"],
        "evidence_hashes": snapshot.get("evidence_hashes", []),
        "included_analysis_run_ids": included,
    }

    # 21. chain_of_custody_summary
    custody_items: list[dict[str, Any]] = []
    for ev in evidence:
        for ce in ev.get("custody_events", []):
            custody_items.append({
                "evidence_id": ev["evidence_id"],
                "evidence_number": ev["evidence_number"],
                **ce,
            })
    sections["chain_of_custody_summary"] = {
        "available": bool(custody_items),
        "count": len(custody_items),
        "items": custody_items,
    }

    # 22. appendix_raw_findings
    sections["appendix_raw_findings"] = {
        "analysis_summaries": summaries,
        "case_intelligence": case_intelligence,
    }

    content: dict[str, Any] = {
        "report_id": report_id,
        "report_version": REPORT_VERSION,
        "engine_version": ENGINE_VERSION,
        "generated_at": generated_at,
        "title": (
            f"Forensic Investigation Report — {case['case_number']}"
        ),
        "section_order": list(SECTION_ORDER),
        "sections": sections,
    }

    content["report_checksum"] = content_checksum(content)

    return content
