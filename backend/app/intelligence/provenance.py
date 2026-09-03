"""Provenance helpers for narrative statements."""

from __future__ import annotations

from typing import Any


def empty_provenance() -> dict[str, list[str]]:
    """Return an empty provenance link set."""

    return {
        "evidence_ids": [],
        "finding_ids": [],
        "fusion_ids": [],
        "timeline_ids": [],
        "correlation_ids": [],
        "entity_ids": [],
        "report_ids": [],
        "audit_ids": [],
    }


def merge_provenance(*parts: dict[str, Any]) -> dict[str, list[str]]:
    """Merge provenance dicts with deterministic unique ordering."""

    merged = empty_provenance()
    for part in parts:
        if not isinstance(part, dict):
            continue
        for key in merged:
            values = part.get(key, [])
            if not isinstance(values, list):
                continue
            for value in values:
                text = str(value)
                if text and text not in merged[key]:
                    merged[key].append(text)
            merged[key].sort()
    return merged


def provenance(
    *,
    evidence_ids: list[str] | None = None,
    finding_ids: list[str] | None = None,
    fusion_ids: list[str] | None = None,
    timeline_ids: list[str] | None = None,
    correlation_ids: list[str] | None = None,
    entity_ids: list[str] | None = None,
    report_ids: list[str] | None = None,
    audit_ids: list[str] | None = None,
) -> dict[str, list[str]]:
    """Build a sorted provenance payload."""

    def _clean(values: list[str] | None) -> list[str]:
        items = [str(item) for item in (values or []) if item]
        return sorted(set(items))

    return {
        "evidence_ids": _clean(evidence_ids),
        "finding_ids": _clean(finding_ids),
        "fusion_ids": _clean(fusion_ids),
        "timeline_ids": _clean(timeline_ids),
        "correlation_ids": _clean(correlation_ids),
        "entity_ids": _clean(entity_ids),
        "report_ids": _clean(report_ids),
        "audit_ids": _clean(audit_ids),
    }


def collect_snapshot_provenance(snapshot: dict[str, Any]) -> dict[str, list[str]]:
    """Extract top-level provenance IDs from an aggregated snapshot."""

    evidence_ids = [str(item["evidence_id"]) for item in snapshot.get("evidence", [])]
    finding_ids: list[str] = []
    for summary in snapshot.get("analysis_summaries", []):
        for finding in summary.get("forensic_findings", []):
            finding_ids.append(str(finding["finding_id"]))
    fusion_ids = [
        str(item["fusion_run_id"])
        for item in snapshot.get("fusion_snapshots", [])
        if item.get("fusion_run_id")
    ]
    timeline_ids: list[str] = []
    timeline = snapshot.get("timeline") or {}
    if timeline.get("run_id"):
        timeline_ids.append(str(timeline["run_id"]))
    for event in timeline.get("items", []):
        if event.get("event_id"):
            timeline_ids.append(str(event["event_id"]))
    correlation_ids: list[str] = []
    correlation = snapshot.get("correlation") or {}
    if correlation.get("run_id"):
        correlation_ids.append(str(correlation["run_id"]))
    entity_ids: list[str] = []
    entities = snapshot.get("entity_resolution") or {}
    if entities.get("run_id"):
        entity_ids.append(str(entities["run_id"]))
    for entity in entities.get("entities", []):
        if entity.get("canonical_id"):
            entity_ids.append(str(entity["canonical_id"]))
    return provenance(
        evidence_ids=evidence_ids,
        finding_ids=finding_ids,
        fusion_ids=fusion_ids,
        timeline_ids=timeline_ids,
        correlation_ids=correlation_ids,
        entity_ids=entity_ids,
    )
