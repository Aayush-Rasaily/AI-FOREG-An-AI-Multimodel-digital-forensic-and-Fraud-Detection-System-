"""Section summarizers for investigation intelligence."""

from __future__ import annotations

from collections import Counter
from typing import Any

from backend.app.intelligence.provenance import provenance


def summarize_overview(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Build case overview statistics from stored evidence metadata."""

    evidence = list(snapshot.get("evidence", []))
    mime_types = Counter(str(item.get("mime_type") or "unknown") for item in evidence)
    processing = Counter(
        str(item.get("processing_status") or "unknown") for item in evidence
    )
    timestamps = [
        item.get("ingested_at")
        for item in evidence
        if isinstance(item.get("ingested_at"), str)
    ]
    analyzed = sum(
        1
        for item in evidence
        if item.get("coverage_status") not in {None, "not_analyzed"}
    )
    case = snapshot.get("case") or {}
    return {
        "case_id": case.get("case_id"),
        "case_number": case.get("case_number"),
        "title": case.get("title"),
        "status": case.get("status"),
        "priority": case.get("priority"),
        "evidence_count": len(evidence),
        "analyzed_count": analyzed,
        "not_analyzed_count": len(evidence) - analyzed,
        "mime_types": dict(sorted(mime_types.items())),
        "processing_statuses": dict(sorted(processing.items())),
        "date_range_start": min(timestamps) if timestamps else None,
        "date_range_end": max(timestamps) if timestamps else None,
        "analysis_coverage": {
            "fusion_runs": len(snapshot.get("fusion_snapshots", [])),
            "has_timeline": bool(snapshot.get("timeline")),
            "has_correlation": bool(snapshot.get("correlation")),
            "has_entity_graph": bool(snapshot.get("entity_resolution")),
            "has_case_intelligence": bool(snapshot.get("case_intelligence")),
        },
        "provenance": provenance(
            evidence_ids=[str(item["evidence_id"]) for item in evidence]
        ),
    }


def summarize_timeline(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Summarize persisted timeline events without regenerating them."""

    timeline = snapshot.get("timeline")
    if not timeline:
        return {
            "available": False,
            "earliest_event": None,
            "latest_event": None,
            "event_count": 0,
            "gaps": [],
            "clusters": [],
            "sequence_anomalies": [],
            "provenance": provenance(),
        }

    items = list(timeline.get("items", []))
    stamped = [item for item in items if item.get("timestamp")]
    stamped.sort(key=lambda row: str(row.get("timestamp")))
    earliest = stamped[0] if stamped else None
    latest = stamped[-1] if stamped else None

    gaps: list[dict[str, Any]] = []
    for left, right in zip(stamped, stamped[1:], strict=False):
        # Record adjacent pairs as potential gap markers when timestamps differ.
        if left.get("timestamp") != right.get("timestamp"):
            gaps.append(
                {
                    "from_event_id": left.get("event_id"),
                    "to_event_id": right.get("event_id"),
                    "from_timestamp": left.get("timestamp"),
                    "to_timestamp": right.get("timestamp"),
                }
            )
    gaps = gaps[:10]

    type_counts = Counter(str(item.get("event_type") or "unknown") for item in items)
    clusters = [
        {"event_type": key, "count": count}
        for key, count in sorted(
            type_counts.items(),
            key=lambda pair: (-pair[1], pair[0]),
        )
    ]

    anomalies = [
        {
            "event_id": item.get("event_id"),
            "reason": "missing_timestamp",
        }
        for item in items
        if not item.get("timestamp")
    ]

    return {
        "available": True,
        "run_id": timeline.get("run_id"),
        "earliest_event": earliest,
        "latest_event": latest,
        "event_count": int(timeline.get("event_count") or len(items)),
        "gaps": gaps,
        "clusters": clusters,
        "sequence_anomalies": anomalies,
        "provenance": provenance(
            timeline_ids=[str(timeline.get("run_id") or "")]
            + [str(item.get("event_id") or "") for item in items],
            evidence_ids=[
                str(item["evidence_id"])
                for item in items
                if item.get("evidence_id")
            ],
        ),
    }


def summarize_correlations(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Summarize persisted cross-evidence relationships."""

    correlation = snapshot.get("correlation")
    entities = snapshot.get("entity_resolution")
    evidence_ids = {str(item["evidence_id"]) for item in snapshot.get("evidence", [])}

    if not correlation:
        connected: set[str] = set()
        return {
            "available": False,
            "strongest": [],
            "cluster_count": 0,
            "disconnected_evidence": sorted(evidence_ids),
            "repeated_identifiers": [],
            "provenance": provenance(),
        }

    items = sorted(
        list(correlation.get("items", [])),
        key=lambda row: (
            -(float(row.get("score") or 0.0)),
            -(float(row.get("confidence") or 0.0)),
            str(row.get("left_evidence_id")),
            str(row.get("right_evidence_id")),
        ),
    )
    strongest = items[:10]
    connected = set()
    for item in items:
        connected.add(str(item.get("left_evidence_id") or ""))
        connected.add(str(item.get("right_evidence_id") or ""))
    connected.discard("")

    repeated: list[dict[str, Any]] = []
    if entities:
        for entity in entities.get("entities", []):
            support = int(entity.get("support_count") or 0)
            if support >= 2:
                repeated.append(
                    {
                        "canonical_id": entity.get("canonical_id"),
                        "display_name": entity.get("display_name"),
                        "entity_type": entity.get("entity_type"),
                        "support_count": support,
                    }
                )
        repeated.sort(
            key=lambda row: (
                -int(row.get("support_count") or 0),
                str(row.get("canonical_id") or ""),
            )
        )

    return {
        "available": True,
        "run_id": correlation.get("run_id"),
        "correlation_count": int(correlation.get("correlation_count") or len(items)),
        "strongest": strongest,
        "cluster_count": len(connected),
        "disconnected_evidence": sorted(evidence_ids - connected),
        "repeated_identifiers": repeated[:20],
        "provenance": provenance(
            correlation_ids=[str(correlation.get("run_id") or "")],
            entity_ids=[str(item.get("canonical_id") or "") for item in repeated],
            evidence_ids=sorted(connected),
        ),
    }


def summarize_ai(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Summarize modality AI and fusion agreement from stored snapshots."""

    counts = {
        "image": 0,
        "document": 0,
        "signature": 0,
        "video": 0,
        "audio": 0,
    }
    for summary in snapshot.get("analysis_summaries", []):
        if summary.get("image_ai"):
            counts["image"] += 1
        if summary.get("document_ai"):
            counts["document"] += 1
        if summary.get("signature_ai"):
            counts["signature"] += 1
        if summary.get("video_ai"):
            counts["video"] += 1
        if summary.get("audio_ai"):
            counts["audio"] += 1

    fusion_rows = list(snapshot.get("fusion_snapshots", []))
    verdicts = Counter(str(item.get("verdict") or "unknown") for item in fusion_rows)
    conflicts = sum(int(item.get("conflicts_count") or 0) for item in fusion_rows)
    confidences = [
        float(item["confidence"])
        for item in fusion_rows
        if isinstance(item.get("confidence"), (int, float))
    ]
    agreement = 0.0
    if verdicts:
        agreement = max(verdicts.values()) / max(sum(verdicts.values()), 1)

    case_intel = snapshot.get("case_intelligence") or {}
    return {
        "modality_counts": counts,
        "fusion": {
            "run_count": len(fusion_rows),
            "verdicts": dict(sorted(verdicts.items())),
            "conflicts_count": conflicts,
            "mean_confidence": (
                round(sum(confidences) / len(confidences), 4) if confidences else None
            ),
            "agreement": round(agreement, 4),
        },
        "case_intelligence": {
            "available": bool(case_intel),
            "verdict": case_intel.get("verdict"),
            "risk_score": case_intel.get("risk_score"),
            "confidence": case_intel.get("confidence"),
        },
        "provenance": provenance(
            evidence_ids=[
                str(item.get("evidence_id") or "")
                for item in snapshot.get("analysis_summaries", [])
            ],
            fusion_ids=[
                str(item.get("fusion_run_id") or "") for item in fusion_rows
            ],
        ),
    }
