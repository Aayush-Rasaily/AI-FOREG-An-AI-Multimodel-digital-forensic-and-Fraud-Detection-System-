"""Deterministic narrative generation with provenance links."""

from __future__ import annotations

from typing import Any

from backend.app.intelligence.provenance import merge_provenance, provenance


def generate_narrative(
    *,
    overview: dict[str, Any],
    key_findings: list[dict[str, Any]],
    timeline_summary: dict[str, Any],
    correlation_summary: dict[str, Any],
    ai_summary: dict[str, Any],
    overall_risk: str,
    overall_confidence: int,
    recommendations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate explainable narrative paragraphs for each section."""

    paragraphs: list[dict[str, Any]] = []

    paragraphs.append(
        {
            "section": "case_overview",
            "text": (
                f"Case '{overview.get('title') or overview.get('case_number')}' "
                f"contains {overview.get('evidence_count', 0)} evidence item(s) "
                f"({overview.get('analyzed_count', 0)} analyzed). "
                f"Ingestion range: {overview.get('date_range_start') or 'n/a'} "
                f"to {overview.get('date_range_end') or 'n/a'}."
            ),
            "provenance": overview.get("provenance") or provenance(),
        }
    )

    if key_findings:
        top = key_findings[0]
        paragraphs.append(
            {
                "section": "key_findings",
                "text": (
                    f"Highest-priority finding: {top.get('title')} "
                    f"(severity={top.get('severity')}). "
                    f"{top.get('summary')} "
                    f"Total prioritized findings: {len(key_findings)}."
                ),
                "provenance": merge_provenance(
                    *(item.get("provenance") or {} for item in key_findings[:5])
                ),
            }
        )
    else:
        paragraphs.append(
            {
                "section": "key_findings",
                "text": "No prioritized forensic or fusion findings are stored yet.",
                "provenance": provenance(),
            }
        )

    if timeline_summary.get("available"):
        earliest = timeline_summary.get("earliest_event") or {}
        latest = timeline_summary.get("latest_event") or {}
        paragraphs.append(
            {
                "section": "timeline_summary",
                "text": (
                    f"Timeline covers {timeline_summary.get('event_count', 0)} "
                    f"event(s). Earliest: {earliest.get('timestamp') or 'n/a'}; "
                    f"latest: {latest.get('timestamp') or 'n/a'}. "
                    f"Sequence anomalies: "
                    f"{len(timeline_summary.get('sequence_anomalies') or [])}."
                ),
                "provenance": timeline_summary.get("provenance") or provenance(),
            }
        )
    else:
        paragraphs.append(
            {
                "section": "timeline_summary",
                "text": "No persisted timeline run is available for this case.",
                "provenance": provenance(),
            }
        )

    if correlation_summary.get("available"):
        paragraphs.append(
            {
                "section": "cross_evidence",
                "text": (
                    f"Detected {correlation_summary.get('correlation_count', 0)} "
                    f"correlation(s) across "
                    f"{correlation_summary.get('cluster_count', 0)} linked "
                    f"evidence item(s). Disconnected evidence: "
                    f"{len(correlation_summary.get('disconnected_evidence') or [])}."
                ),
                "provenance": correlation_summary.get("provenance") or provenance(),
            }
        )
    else:
        paragraphs.append(
            {
                "section": "cross_evidence",
                "text": "No persisted correlation run is available for this case.",
                "provenance": provenance(),
            }
        )

    fusion = ai_summary.get("fusion") or {}
    modalities = ai_summary.get("modality_counts") or {}
    paragraphs.append(
        {
            "section": "ai_summary",
            "text": (
                "Modality AI coverage — "
                f"image={modalities.get('image', 0)}, "
                f"document={modalities.get('document', 0)}, "
                f"signature={modalities.get('signature', 0)}, "
                f"video={modalities.get('video', 0)}, "
                f"audio={modalities.get('audio', 0)}. "
                f"Fusion runs={fusion.get('run_count', 0)}, "
                f"agreement={fusion.get('agreement')}, "
                f"conflicts={fusion.get('conflicts_count', 0)}."
            ),
            "provenance": ai_summary.get("provenance") or provenance(),
        }
    )

    paragraphs.append(
        {
            "section": "risk_assessment",
            "text": (
                f"Overall case risk is '{overall_risk}' with confidence "
                f"{overall_confidence}/100 based on stored fusion scores, "
                "finding severity, and analysis coverage."
            ),
            "provenance": merge_provenance(
                overview.get("provenance") or {},
                ai_summary.get("provenance") or {},
            ),
        }
    )

    if recommendations:
        top_recs = ", ".join(item["title"] for item in recommendations[:3])
        paragraphs.append(
            {
                "section": "recommended_next_steps",
                "text": (
                    f"{len(recommendations)} deterministic recommendation(s) "
                    f"were generated. Top items: {top_recs}."
                ),
                "provenance": merge_provenance(
                    *(item.get("provenance") or {} for item in recommendations[:5])
                ),
            }
        )

    return paragraphs
