"""Deterministic report provenance helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any

SECTION_ORDER: tuple[str, ...] = (
    "case_summary",
    "evidence_inventory",
    "metadata_summary",
    "ocr_summary",
    "pattern_extraction_summary",
    "timeline",
    "forensic_findings",
    "evidence_comparison",
    "image_ai",
    "document_ai",
    "signature_ai",
    "video_ai",
    "audio_ai",
    "fusion_assessment",
    "correlation_summary",
    "entity_graph_summary",
    "overall_confidence",
    "risk_assessment",
    "conflicts",
    "provenance_summary",
    "chain_of_custody_summary",
    "appendix_raw_findings",
)


def canonical_json(payload: Any) -> str:
    """Serialize JSON with sorted keys for checksum stability."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def content_checksum(content: dict[str, Any]) -> str:
    """SHA-256 of deterministic report content.

    Excludes wall-clock `generated_at` and the checksum field itself.
    """

    payload = {
        key: value
        for key, value in content.items()
        if key not in {"generated_at", "report_checksum"}
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def build_report_provenance(
    *,
    case_id: str,
    case_number: str,
    evidence_hashes: list[str],
    included_analysis_run_ids: dict[str, Any],
    engine_version: str,
    report_version: str,
    policy_versions: dict[str, Any],
    checksum: str,
) -> dict[str, Any]:
    included = dict(included_analysis_run_ids)
    fusion_run_ids = list(included.get("fusion_run_ids") or [])
    return {
        "case_id": case_id,
        "case_number": case_number,
        "evidence_hashes": list(evidence_hashes),
        "included_analysis_run_ids": included,
        # Phase 6I / 6H consumers expect fusion run IDs at the top level.
        "fusion_run_ids": fusion_run_ids,
        "case_intelligence_run_id": included.get("case_intelligence_run_id"),
        "timeline_run_id": included.get("timeline_run_id"),
        "correlation_run_id": included.get("correlation_run_id"),
        "entity_resolution_run_id": included.get("entity_resolution_run_id"),
        "engine_version": engine_version,
        "report_version": report_version,
        "policy_versions": policy_versions,
        "report_checksum": checksum,
        "inference": "none",
    }
