"""Deterministic evidence-gap detection."""

from __future__ import annotations

import hashlib
from typing import Any

from backend.app.investigation_intelligence.models import (
    CoverageMetrics,
    EvidenceGapRecord,
    GapSeverity,
    GapType,
    ProvenanceBundle,
    RecommendationCode,
)


def _key(gap_type: str, *parts: str) -> str:
    material = "|".join((gap_type, *parts))
    digest = hashlib.sha256(material.encode()).hexdigest()
    return f"gap_{digest[:24]}"


def detect_gaps(
    snapshot: dict[str, Any],
    coverage: CoverageMetrics,
) -> list[EvidenceGapRecord]:
    """Identify investigation gaps from existing outputs only."""

    gaps: list[EvidenceGapRecord] = []
    evidence = snapshot.get("evidence", [])
    extractions = {str(item["evidence_id"]) for item in snapshot.get("extractions", [])}
    ai_by_evidence = {
        str(item["evidence_id"]) for item in snapshot.get("ai_findings", [])
    }
    signatures = {
        str(item["evidence_id"])
        for item in snapshot.get("signatures", [])
        if item.get("evidence_id")
    }
    custody = snapshot.get("custody_by_evidence", {})
    has_timeline = bool(snapshot.get("timeline_events"))
    has_graph = bool(snapshot.get("graph_entities"))
    correlations = snapshot.get("correlations", [])

    def add(
        gap_type: GapType,
        *,
        severity: GapSeverity,
        reason: str,
        action: RecommendationCode,
        affected: list[str],
        detail: str | None = None,
    ) -> None:
        gaps.append(
            EvidenceGapRecord(
                gap_key=_key(gap_type.value, *sorted(affected)[:12], reason),
                gap_type=gap_type,
                severity=severity,
                reason=reason,
                recommended_action=action,
                affected_evidence_ids=sorted(set(affected)),
                provenance=ProvenanceBundle(
                    evidence_ids=tuple(sorted(set(affected))),
                    detail=detail or reason,
                ),
            )
        )

    for item in evidence:
        eid = str(item["id"])
        if item.get("missing_original"):
            add(
                GapType.MISSING_ORIGINAL_FILE,
                severity=GapSeverity.HIGH,
                reason="Original file bytes or storage key is missing.",
                action=RecommendationCode.ACQUIRE_ORIGINAL_MEDIA,
                affected=[eid],
            )
        if not item.get("has_metadata"):
            add(
                GapType.MISSING_METADATA,
                severity=GapSeverity.MEDIUM,
                reason="Evidence metadata is incomplete.",
                action=RecommendationCode.OBTAIN_DEVICE_METADATA,
                affected=[eid],
            )
        if not item.get("has_timestamp"):
            add(
                GapType.MISSING_TIMESTAMP,
                severity=GapSeverity.MEDIUM,
                reason="Evidence lacks a reliable capture/upload timestamp.",
                action=RecommendationCode.OBTAIN_DEVICE_METADATA,
                affected=[eid],
            )
        if int(custody.get(eid, 0) or 0) == 0:
            add(
                GapType.MISSING_CHAIN_OF_CUSTODY,
                severity=GapSeverity.HIGH,
                reason="No chain-of-custody events recorded.",
                action=RecommendationCode.VERIFY_CHAIN_OF_CUSTODY,
                affected=[eid],
            )
        mime = str(item.get("mime_type") or "").lower()
        is_doc = "pdf" in mime or "document" in mime or mime.startswith("text/")
        is_image = mime.startswith("image/")
        if is_doc and eid not in extractions:
            add(
                GapType.MISSING_OCR,
                severity=GapSeverity.MEDIUM,
                reason="Document evidence has no OCR/extraction record.",
                action=RecommendationCode.RUN_OCR,
                affected=[eid],
            )
        if (is_doc or is_image) and eid not in ai_by_evidence:
            add(
                GapType.MISSING_AI_ANALYSIS,
                severity=GapSeverity.MEDIUM,
                reason="No AI analysis findings for this evidence.",
                action=RecommendationCode.RUN_AI_ANALYSIS,
                affected=[eid],
            )
        if is_doc and eid not in signatures:
            add(
                GapType.MISSING_SIGNATURE_VERIFICATION,
                severity=GapSeverity.LOW,
                reason="Document has no signature verification run.",
                action=RecommendationCode.VERIFY_DIGITAL_SIGNATURE,
                affected=[eid],
            )

    if len(evidence) >= 2 and not correlations:
        add(
            GapType.MISSING_CORROBORATING_EVIDENCE,
            severity=GapSeverity.MEDIUM,
            reason="No cross-evidence correlations were recorded.",
            action=RecommendationCode.COMPARE_KNOWN_EVIDENCE,
            affected=[str(item["id"]) for item in evidence],
        )

    if evidence and not has_timeline:
        add(
            GapType.MISSING_TIMELINE_EVENT,
            severity=GapSeverity.MEDIUM,
            reason="Investigation timeline has not been generated.",
            action=RecommendationCode.GENERATE_TIMELINE,
            affected=[str(item["id"]) for item in evidence],
        )

    if evidence and not has_graph:
        add(
            GapType.MISSING_GRAPH_RELATIONSHIP,
            severity=GapSeverity.LOW,
            reason="Knowledge graph has not been built for this case.",
            action=RecommendationCode.BUILD_KNOWLEDGE_GRAPH,
            affected=[str(item["id"]) for item in evidence],
        )

    if len(evidence) == 1:
        add(
            GapType.MISSING_COMPARISON_TARGET,
            severity=GapSeverity.MEDIUM,
            reason="Only one evidence item exists; comparison target missing.",
            action=RecommendationCode.COLLECT_CORROBORATING_EVIDENCE,
            affected=[str(evidence[0]["id"])],
        )

    if coverage.open_conflicts > 0:
        add(
            GapType.MISSING_CORROBORATING_EVIDENCE,
            severity=GapSeverity.HIGH,
            reason="Open conflicts require additional corroborating evidence.",
            action=RecommendationCode.REVIEW_CONFLICTING_AI,
            affected=[str(item["id"]) for item in evidence],
            detail=f"open_conflicts={coverage.open_conflicts}",
        )

    gaps.sort(
        key=lambda item: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[item.severity.value],
            item.gap_type.value,
            item.gap_key,
        )
    )
    seen: set[str] = set()
    unique: list[EvidenceGapRecord] = []
    for item in gaps:
        if item.gap_key in seen:
            continue
        seen.add(item.gap_key)
        unique.append(item)
    return unique
