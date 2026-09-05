"""Provenance helpers for decision support artifacts."""

from __future__ import annotations

from typing import Any

from backend.app.decision_support.models import ProvenanceBundle
from backend.app.decision_support.policy import DS_ENGINE_VERSION, DS_POLICY_VERSION


def provenance_to_dict(bundle: ProvenanceBundle) -> dict[str, Any]:
    return {
        "evidence_ids": list(bundle.evidence_ids),
        "timeline_ids": list(bundle.timeline_ids),
        "correlation_ids": list(bundle.correlation_ids),
        "fusion_ids": list(bundle.fusion_ids),
        "knowledge_graph_ids": list(bundle.knowledge_graph_ids),
        "hypothesis_ids": list(bundle.hypothesis_ids),
        "recommendation_ids": list(bundle.recommendation_ids),
        "gap_ids": list(bundle.gap_ids),
        "detail": bundle.detail,
        "engine_version": DS_ENGINE_VERSION,
        "policy_version": DS_POLICY_VERSION,
    }
