"""Deterministic evidence/case validation signals from existing outputs."""

from __future__ import annotations

from typing import Any


def evaluate_signals(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return boolean/count signals used by checklist generation."""

    evidence = snapshot.get("evidence") or []
    custody = snapshot.get("custody_by_evidence") or {}
    with_hash = sum(1 for item in evidence if item.get("sha256_hash"))
    with_meta = sum(1 for item in evidence if item.get("has_metadata"))
    with_custody = sum(
        1 for item in evidence if int(custody.get(str(item["id"]), 0) or 0) > 0
    )
    return {
        "evidence_total": len(evidence),
        "evidence_with_hash": with_hash,
        "evidence_with_metadata": with_meta,
        "evidence_with_custody": with_custody,
        "has_timeline": bool(snapshot.get("timeline_events")),
        "timeline_conflicts": len(snapshot.get("timeline_conflicts") or []),
        "has_ai_findings": bool(snapshot.get("ai_findings")),
        "has_fusion": bool(snapshot.get("fusion_runs")),
        "fusion_conflicts": len(snapshot.get("fusion_conflicts") or []),
        "has_correlations": bool(snapshot.get("correlations")),
        "has_knowledge_graph": bool(snapshot.get("knowledge_graph_ids")),
        "has_hypotheses": bool(snapshot.get("hypotheses")),
        "has_recommendations": bool(snapshot.get("recommendations")),
        "has_reports": bool(snapshot.get("reports")),
        "open_workflow_tasks": int(snapshot.get("open_workflow_tasks") or 0),
        "workflow_completion": float(snapshot.get("workflow_completion") or 0),
        "open_conflicts": len(snapshot.get("open_conflicts") or []),
    }
