"""Provenance helpers for knowledge-graph edges and entities."""

from __future__ import annotations

from typing import Any

from backend.app.knowledge_graph.models import GraphProvenanceRef
from backend.app.knowledge_graph.policy import KG_ENGINE_VERSION, KG_POLICY_VERSION


def provenance_to_dict(ref: GraphProvenanceRef) -> dict[str, Any]:
    return {
        "source_kind": ref.source_kind,
        "source_id": ref.source_id,
        "evidence_id": ref.evidence_id,
        "finding_id": ref.finding_id,
        "timeline_id": ref.timeline_id,
        "correlation_id": ref.correlation_id,
        "fusion_id": ref.fusion_id,
        "ocr_field": ref.ocr_field,
        "metadata_field": ref.metadata_field,
        "timestamp": ref.timestamp,
        "detail": ref.detail,
        "engine_version": KG_ENGINE_VERSION,
        "policy_version": KG_POLICY_VERSION,
    }


def merge_provenance(
    left: tuple[GraphProvenanceRef, ...],
    right: tuple[GraphProvenanceRef, ...],
) -> tuple[GraphProvenanceRef, ...]:
    """Merge provenance refs with deterministic unique ordering."""

    seen: set[tuple[str, str, str | None]] = set()
    merged: list[GraphProvenanceRef] = []
    for ref in (*left, *right):
        key = (ref.source_kind, ref.source_id, ref.evidence_id)
        if key in seen:
            continue
        seen.add(key)
        merged.append(ref)
    return tuple(
        sorted(
            merged,
            key=lambda item: (
                item.source_kind,
                item.source_id,
                item.evidence_id or "",
            ),
        )
    )
