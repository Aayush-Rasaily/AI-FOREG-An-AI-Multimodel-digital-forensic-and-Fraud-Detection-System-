"""Provenance helpers for case review."""

from __future__ import annotations

from typing import Any

from backend.app.case_review.models import ProvenanceBundle
from backend.app.case_review.policy import CR_ENGINE_VERSION, CR_POLICY_VERSION


def provenance_to_dict(bundle: ProvenanceBundle) -> dict[str, Any]:
    return {
        "evidence_ids": list(bundle.evidence_ids),
        "timeline_ids": list(bundle.timeline_ids),
        "correlation_ids": list(bundle.correlation_ids),
        "fusion_ids": list(bundle.fusion_ids),
        "knowledge_graph_ids": list(bundle.knowledge_graph_ids),
        "workflow_task_ids": list(bundle.workflow_task_ids),
        "hypothesis_ids": list(bundle.hypothesis_ids),
        "recommendation_ids": list(bundle.recommendation_ids),
        "report_ids": list(bundle.report_ids),
        "detail": bundle.detail,
        "engine_version": CR_ENGINE_VERSION,
        "policy_version": CR_POLICY_VERSION,
    }
