"""Deterministic evidence review-queue construction."""

from __future__ import annotations

import hashlib
from typing import Any

from backend.app.decision_support.models import (
    ProvenanceBundle,
    ReviewQueueDraft,
)
from backend.app.decision_support.scoring import (
    priority_from_score,
    review_priority_score,
)

REASON_WEIGHTS: dict[str, float] = {
    "high_ai_disagreement": 0.95,
    "unresolved_conflict": 0.92,
    "low_confidence_fusion": 0.88,
    "missing_metadata": 0.70,
    "unresolved_correlation": 0.72,
    "incomplete_custody": 0.90,
    "investigation_gap": 0.80,
}


def _key(evidence_id: str, *reasons: str) -> str:
    material = "|".join((evidence_id, *sorted(reasons)))
    digest = hashlib.sha256(material.encode()).hexdigest()
    return f"dsrev_{digest[:24]}"


def build_review_queue(snapshot: dict[str, Any]) -> list[ReviewQueueDraft]:
    """Prioritize evidence requiring investigator review."""

    by_evidence: dict[str, list[str]] = {}

    def add(evidence_id: str, reason: str) -> None:
        if not evidence_id:
            return
        by_evidence.setdefault(evidence_id, [])
        if reason not in by_evidence[evidence_id]:
            by_evidence[evidence_id].append(reason)

    for conflict in snapshot.get("open_conflicts", []):
        kind = str(conflict.get("kind") or "")
        if kind == "fusion":
            # Associate with all evidence when specific id unknown
            for item in snapshot.get("evidence", []):
                add(str(item["id"]), "unresolved_conflict")
                add(str(item["id"]), "high_ai_disagreement")
        elif kind == "timeline":
            for eid in conflict.get("evidence_ids") or []:
                add(str(eid), "unresolved_conflict")
            if not conflict.get("evidence_ids"):
                for item in snapshot.get("evidence", []):
                    add(str(item["id"]), "unresolved_conflict")

    for run in snapshot.get("fusion_runs", []):
        conf = float(run.get("confidence") or 1.0)
        if conf < 0.5 or float(run.get("risk_score") or 0) >= 0.7:
            add(str(run.get("evidence_id") or ""), "low_confidence_fusion")

    custody = snapshot.get("custody_by_evidence") or {}
    for item in snapshot.get("evidence", []):
        eid = str(item["id"])
        if not item.get("has_metadata"):
            add(eid, "missing_metadata")
        if int(custody.get(eid, 0) or 0) == 0:
            add(eid, "incomplete_custody")

    if not snapshot.get("correlations") and len(snapshot.get("evidence", [])) >= 2:
        for item in snapshot.get("evidence", []):
            add(str(item["id"]), "unresolved_correlation")

    for gap in snapshot.get("gaps", []):
        for eid in gap.get("affected_evidence_ids") or []:
            add(str(eid), "investigation_gap")

    queue: list[ReviewQueueDraft] = []
    for evidence_id, reasons in sorted(by_evidence.items()):
        weights = [REASON_WEIGHTS[r] for r in reasons if r in REASON_WEIGHTS]
        score = review_priority_score(weights)
        queue.append(
            ReviewQueueDraft(
                queue_key=_key(evidence_id, *reasons),
                evidence_id=evidence_id,
                priority=priority_from_score(score),
                priority_score=score,
                reasons=sorted(reasons),
                provenance=ProvenanceBundle(
                    evidence_ids=(evidence_id,),
                    detail=",".join(sorted(reasons)),
                ),
            )
        )

    queue.sort(
        key=lambda item: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[item.priority.value],
            -item.priority_score,
            item.evidence_id,
            item.queue_key,
        )
    )
    return queue
