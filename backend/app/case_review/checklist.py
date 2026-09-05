"""Deterministic review checklist generation."""

from __future__ import annotations

import hashlib
from typing import Any

from backend.app.case_review.models import (
    ChecklistItemDraft,
    ChecklistItemStatus,
    ProvenanceBundle,
)
from backend.app.case_review.policy import CHECKLIST_ITEMS
from backend.app.case_review.validation import evaluate_signals


def _key(code: str, *parts: str) -> str:
    material = "|".join((code, *parts))
    digest = hashlib.sha256(material.encode()).hexdigest()
    return f"critem_{digest[:24]}"


def generate_checklist(snapshot: dict[str, Any]) -> list[ChecklistItemDraft]:
    """Build checklist items with suggested statuses (never auto-approved)."""

    signals = evaluate_signals(snapshot)
    evidence_ids = tuple(
        sorted(str(item["id"]) for item in snapshot.get("evidence") or [])
    )
    items: list[ChecklistItemDraft] = []

    def add(
        code: str,
        title: str,
        *,
        suggested: ChecklistItemStatus,
        blocking: bool,
        outstanding: bool,
        notes: str,
        provenance: ProvenanceBundle | None = None,
    ) -> None:
        items.append(
            ChecklistItemDraft(
                item_key=_key(code, suggested.value, notes[:40]),
                item_code=code,
                title=title,
                status=ChecklistItemStatus.PENDING,
                suggested_status=suggested,
                blocking=blocking,
                outstanding=outstanding,
                notes=notes,
                provenance=provenance
                or ProvenanceBundle(evidence_ids=evidence_ids, detail=notes),
            )
        )

    total = signals["evidence_total"]
    if total == 0:
        add(
            "EVIDENCE_INTEGRITY",
            "Evidence Integrity",
            suggested=ChecklistItemStatus.FAIL,
            blocking=True,
            outstanding=True,
            notes="No evidence registered for this case.",
        )
    else:
        add(
            "EVIDENCE_INTEGRITY",
            "Evidence Integrity",
            suggested=(
                ChecklistItemStatus.PASS
                if signals["evidence_with_hash"] == total
                else ChecklistItemStatus.FAIL
            ),
            blocking=signals["evidence_with_hash"] < total,
            outstanding=signals["evidence_with_hash"] < total,
            notes=(
                f"{signals['evidence_with_hash']}/{total} evidence items "
                "have SHA-256 hashes."
            ),
        )

    add(
        "SHA256_VERIFIED",
        "SHA256 Verified",
        suggested=(
            ChecklistItemStatus.PASS
            if total and signals["evidence_with_hash"] == total
            else ChecklistItemStatus.FAIL
            if total
            else ChecklistItemStatus.NA
        ),
        blocking=bool(total and signals["evidence_with_hash"] < total),
        outstanding=bool(total and signals["evidence_with_hash"] < total),
        notes="SHA-256 presence check against stored evidence records.",
    )
    add(
        "METADATA_VERIFIED",
        "Metadata Verified",
        suggested=(
            ChecklistItemStatus.PASS
            if total and signals["evidence_with_metadata"] == total
            else ChecklistItemStatus.FAIL
            if total
            else ChecklistItemStatus.NA
        ),
        blocking=False,
        outstanding=bool(total and signals["evidence_with_metadata"] < total),
        notes=(
            f"{signals['evidence_with_metadata']}/{total} evidence items have metadata."
        ),
    )
    add(
        "CHAIN_OF_CUSTODY_COMPLETE",
        "Chain of Custody Complete",
        suggested=(
            ChecklistItemStatus.PASS
            if total and signals["evidence_with_custody"] == total
            else ChecklistItemStatus.FAIL
            if total
            else ChecklistItemStatus.NA
        ),
        blocking=bool(total and signals["evidence_with_custody"] < total),
        outstanding=bool(total and signals["evidence_with_custody"] < total),
        notes=(
            f"{signals['evidence_with_custody']}/{total} evidence items "
            "have custody events."
        ),
    )
    add(
        "TIMELINE_REVIEWED",
        "Timeline Reviewed",
        suggested=(
            ChecklistItemStatus.PASS
            if signals["has_timeline"] and signals["timeline_conflicts"] == 0
            else ChecklistItemStatus.FAIL
            if signals["timeline_conflicts"]
            else ChecklistItemStatus.PENDING
        ),
        blocking=signals["timeline_conflicts"] > 0,
        outstanding=not signals["has_timeline"] or signals["timeline_conflicts"] > 0,
        notes=(
            "Timeline conflicts present."
            if signals["timeline_conflicts"]
            else (
                "Timeline available for review."
                if signals["has_timeline"]
                else "Timeline not generated."
            )
        ),
        provenance=ProvenanceBundle(
            evidence_ids=evidence_ids,
            timeline_ids=tuple(
                sorted(
                    str(item["id"]) for item in snapshot.get("timeline_events") or []
                )
            ),
            detail="timeline",
        ),
    )
    add(
        "AI_FINDINGS_REVIEWED",
        "AI Findings Reviewed",
        suggested=(
            ChecklistItemStatus.PASS
            if signals["has_ai_findings"]
            else ChecklistItemStatus.PENDING
        ),
        blocking=False,
        outstanding=not signals["has_ai_findings"],
        notes=(
            "AI findings available for reviewer confirmation."
            if signals["has_ai_findings"]
            else "No AI findings recorded."
        ),
    )
    add(
        "FUSION_REVIEWED",
        "Fusion Reviewed",
        suggested=(
            ChecklistItemStatus.FAIL
            if signals["fusion_conflicts"]
            else ChecklistItemStatus.PASS
            if signals["has_fusion"]
            else ChecklistItemStatus.PENDING
        ),
        blocking=signals["fusion_conflicts"] > 0,
        outstanding=not signals["has_fusion"] or signals["fusion_conflicts"] > 0,
        notes=(
            "Fusion conflicts require review."
            if signals["fusion_conflicts"]
            else (
                "Fusion runs available." if signals["has_fusion"] else "No fusion runs."
            )
        ),
        provenance=ProvenanceBundle(
            evidence_ids=evidence_ids,
            fusion_ids=tuple(
                sorted(str(item["id"]) for item in snapshot.get("fusion_runs") or [])
            ),
            detail="fusion",
        ),
    )
    add(
        "CORRELATIONS_REVIEWED",
        "Correlations Reviewed",
        suggested=(
            ChecklistItemStatus.PASS
            if signals["has_correlations"]
            else ChecklistItemStatus.PENDING
        ),
        blocking=False,
        outstanding=not signals["has_correlations"] and total >= 2,
        notes=(
            "Correlations available."
            if signals["has_correlations"]
            else "No correlations recorded."
        ),
        provenance=ProvenanceBundle(
            evidence_ids=evidence_ids,
            correlation_ids=tuple(
                sorted(str(item["id"]) for item in snapshot.get("correlations") or [])
            ),
            detail="correlation",
        ),
    )
    add(
        "KNOWLEDGE_GRAPH_REVIEWED",
        "Knowledge Graph Reviewed",
        suggested=(
            ChecklistItemStatus.PASS
            if signals["has_knowledge_graph"]
            else ChecklistItemStatus.PENDING
        ),
        blocking=False,
        outstanding=not signals["has_knowledge_graph"],
        notes=(
            "Knowledge graph available."
            if signals["has_knowledge_graph"]
            else "Knowledge graph not built."
        ),
        provenance=ProvenanceBundle(
            evidence_ids=evidence_ids,
            knowledge_graph_ids=tuple(snapshot.get("knowledge_graph_ids") or ()),
            detail="knowledge_graph",
        ),
    )
    add(
        "HYPOTHESES_REVIEWED",
        "Hypotheses Reviewed",
        suggested=(
            ChecklistItemStatus.PASS
            if signals["has_hypotheses"]
            else ChecklistItemStatus.PENDING
        ),
        blocking=False,
        outstanding=not signals["has_hypotheses"],
        notes=(
            "Investigation hypotheses available."
            if signals["has_hypotheses"]
            else "No hypotheses persisted."
        ),
        provenance=ProvenanceBundle(
            evidence_ids=evidence_ids,
            hypothesis_ids=tuple(
                sorted(
                    str(item.get("hypothesis_key") or "")
                    for item in snapshot.get("hypotheses") or []
                )
            ),
            detail="hypotheses",
        ),
    )
    add(
        "RECOMMENDATIONS_REVIEWED",
        "Recommendations Reviewed",
        suggested=(
            ChecklistItemStatus.PASS
            if signals["has_recommendations"]
            else ChecklistItemStatus.PENDING
        ),
        blocking=False,
        outstanding=not signals["has_recommendations"],
        notes=(
            "Recommendations available."
            if signals["has_recommendations"]
            else "No recommendations persisted."
        ),
        provenance=ProvenanceBundle(
            evidence_ids=evidence_ids,
            recommendation_ids=tuple(
                sorted(
                    str(item.get("recommendation_key") or "")
                    for item in snapshot.get("recommendations") or []
                )
            ),
            detail="recommendations",
        ),
    )
    add(
        "REPORT_REVIEWED",
        "Report Reviewed",
        suggested=(
            ChecklistItemStatus.PASS
            if signals["has_reports"]
            else ChecklistItemStatus.PENDING
        ),
        blocking=False,
        outstanding=not signals["has_reports"],
        notes=(
            "Forensic reports available."
            if signals["has_reports"]
            else "No forensic reports."
        ),
        provenance=ProvenanceBundle(
            evidence_ids=evidence_ids,
            report_ids=tuple(
                sorted(str(item["id"]) for item in snapshot.get("reports") or [])
            ),
            detail="reports",
        ),
    )

    workflow_ok = signals["open_workflow_tasks"] == 0 and (
        signals["workflow_completion"] >= 0.8 or not signals["open_workflow_tasks"]
    )
    final_pass = (
        total > 0
        and signals["evidence_with_hash"] == total
        and signals["evidence_with_custody"] == total
        and signals["timeline_conflicts"] == 0
        and signals["fusion_conflicts"] == 0
        and signals["open_conflicts"] == 0
    )
    add(
        "FINAL_VALIDATION",
        "Final Validation",
        suggested=(
            ChecklistItemStatus.PASS
            if final_pass and workflow_ok
            else ChecklistItemStatus.BLOCKED
            if not final_pass
            else ChecklistItemStatus.PENDING
        ),
        blocking=not final_pass,
        outstanding=not final_pass,
        notes=(
            "Ready for final validation pending reviewer confirmation."
            if final_pass
            else "Blocking integrity/conflict issues remain."
        ),
        provenance=ProvenanceBundle(
            evidence_ids=evidence_ids,
            workflow_task_ids=tuple(snapshot.get("workflow_task_ids") or ()),
            detail="final_validation",
        ),
    )

    # Ensure all policy checklist codes exist (deterministic order)
    by_code = {item.item_code: item for item in items}
    ordered: list[ChecklistItemDraft] = []
    for code, title in CHECKLIST_ITEMS:
        if code in by_code:
            ordered.append(by_code[code])
        else:
            ordered.append(
                ChecklistItemDraft(
                    item_key=_key(code, "PENDING"),
                    item_code=code,
                    title=title,
                    status=ChecklistItemStatus.PENDING,
                    suggested_status=ChecklistItemStatus.PENDING,
                    blocking=False,
                    outstanding=True,
                    notes="Awaiting review.",
                    provenance=ProvenanceBundle(evidence_ids=evidence_ids),
                )
            )
    return ordered
