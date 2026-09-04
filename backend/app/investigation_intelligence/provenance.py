"""Provenance helpers for investigation intelligence artifacts."""

from __future__ import annotations

from typing import Any

from backend.app.investigation_intelligence.models import ProvenanceBundle
from backend.app.investigation_intelligence.policy import (
    II_ENGINE_VERSION,
    II_POLICY_VERSION,
)


def provenance_to_dict(bundle: ProvenanceBundle) -> dict[str, Any]:
    return {
        "evidence_ids": list(bundle.evidence_ids),
        "timeline_ids": list(bundle.timeline_ids),
        "graph_node_ids": list(bundle.graph_node_ids),
        "correlation_ids": list(bundle.correlation_ids),
        "fusion_ids": list(bundle.fusion_ids),
        "ai_finding_ids": list(bundle.ai_finding_ids),
        "report_ids": list(bundle.report_ids),
        "detail": bundle.detail,
        "engine_version": II_ENGINE_VERSION,
        "policy_version": II_POLICY_VERSION,
    }


def merge_id_tuples(*groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for group in groups:
        for item in group:
            if item and item not in seen:
                seen.add(item)
                ordered.append(item)
    return tuple(sorted(ordered))
