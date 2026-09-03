"""Provenance helpers for entity resolution."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.app.entities.policy import ENGINE_VERSION, POLICY_VERSION


def build_run_provenance(
    *,
    case_id: UUID,
    case_number: str,
    evidence_count: int,
    entity_count: int,
    relationship_count: int,
) -> dict[str, Any]:
    return {
        "case_id": str(case_id),
        "case_number": case_number,
        "engine_version": ENGINE_VERSION,
        "policy_version": POLICY_VERSION,
        "evidence_count": evidence_count,
        "entity_count": entity_count,
        "relationship_count": relationship_count,
        "inference": "none",
    }


def build_entity_provenance(
    *,
    case_id: UUID,
    entity_type: str,
    normalized_key: str,
    evidence_ids: list[str],
    extraction_ids: list[str] | None = None,
    finding_ids: list[str] | None = None,
    correlation_ids: list[str] | None = None,
    timeline_ids: list[str] | None = None,
    fusion_ids: list[str] | None = None,
    metadata_fields: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "case_id": str(case_id),
        "entity_type": entity_type,
        "normalized_key": normalized_key,
        "evidence_ids": sorted(evidence_ids),
        "extraction_ids": sorted(extraction_ids or []),
        "finding_ids": sorted(finding_ids or []),
        "correlation_ids": sorted(correlation_ids or []),
        "timeline_ids": sorted(timeline_ids or []),
        "fusion_ids": sorted(fusion_ids or []),
        "metadata_fields": sorted(metadata_fields or []),
        "policy_version": POLICY_VERSION,
        "engine_version": ENGINE_VERSION,
    }


def build_edge_provenance(
    *,
    case_id: UUID,
    relationship_type: str,
    source_canonical_id: str,
    target_canonical_id: str,
    evidence_ids: list[str],
    extraction_ids: list[str] | None = None,
    finding_ids: list[str] | None = None,
    correlation_ids: list[str] | None = None,
    timeline_ids: list[str] | None = None,
    fusion_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "case_id": str(case_id),
        "relationship_type": relationship_type,
        "source_canonical_id": source_canonical_id,
        "target_canonical_id": target_canonical_id,
        "evidence_ids": sorted(evidence_ids),
        "extraction_ids": sorted(extraction_ids or []),
        "finding_ids": sorted(finding_ids or []),
        "correlation_ids": sorted(correlation_ids or []),
        "timeline_ids": sorted(timeline_ids or []),
        "fusion_ids": sorted(fusion_ids or []),
        "policy_version": POLICY_VERSION,
        "engine_version": ENGINE_VERSION,
    }


def canonical_entity_key(entity_type: str, normalized_key: str) -> str:
    return f"{entity_type}:{normalized_key}"


def relationship_key(
    source_canonical_id: str,
    target_canonical_id: str,
    relationship_type: str,
) -> str:
    return f"{source_canonical_id}|{relationship_type}|{target_canonical_id}"


def format_canonical_id(index: int) -> str:
    return f"ENTITY-{index:06d}"
