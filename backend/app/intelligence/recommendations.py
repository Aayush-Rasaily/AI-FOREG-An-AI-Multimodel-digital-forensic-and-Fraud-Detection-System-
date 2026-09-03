"""Deterministic recommendation generation."""

from __future__ import annotations

from typing import Any

from backend.app.intelligence.models import RecommendationCode
from backend.app.intelligence.provenance import provenance


def generate_recommendations(
    snapshot: dict[str, Any],
    key_findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Produce explainable next-step recommendations from stored data."""

    recommendations: list[dict[str, Any]] = []
    evidence = list(snapshot.get("evidence", []))
    evidence_ids = [str(item["evidence_id"]) for item in evidence]

    not_analyzed = [
        item
        for item in evidence
        if item.get("coverage_status") in {None, "not_analyzed"}
    ]
    if not_analyzed:
        ids = [str(item["evidence_id"]) for item in not_analyzed]
        recommendations.append(
            {
                "code": RecommendationCode.RUN_ANALYSIS.value,
                "title": "Complete missing analyses",
                "rationale": (
                    f"{len(not_analyzed)} evidence item(s) have not been "
                    "analyzed by fusion or case intelligence."
                ),
                "supporting_finding_refs": [
                    item["title"]
                    for item in key_findings
                    if item["title"] == "unavailable_analyses"
                ],
                "provenance": provenance(evidence_ids=ids),
            }
        )

    low_res = [
        item
        for item in evidence
        if str(item.get("mime_type") or "").startswith("image/")
        and isinstance(item.get("file_size"), int)
        and item["file_size"] < 50_000
    ]
    if low_res:
        recommendations.append(
            {
                "code": RecommendationCode.HIGHER_RESOLUTION.value,
                "title": "Obtain higher resolution",
                "rationale": (
                    "One or more image evidence files are unusually small, "
                    "which may limit forensic detector reliability."
                ),
                "supporting_finding_refs": [],
                "provenance": provenance(
                    evidence_ids=[str(item["evidence_id"]) for item in low_res]
                ),
            }
        )

    signature_touched = any(
        summary.get("signature_ai")
        for summary in snapshot.get("analysis_summaries", [])
    )
    if signature_touched:
        sig_ids = [
            str(summary["evidence_id"])
            for summary in snapshot.get("analysis_summaries", [])
            if summary.get("signature_ai")
        ]
        recommendations.append(
            {
                "code": RecommendationCode.VERIFY_SIGNATURE.value,
                "title": "Verify signature manually",
                "rationale": (
                    "Signature AI results are present; manual verification "
                    "is recommended for evidentiary confirmation."
                ),
                "supporting_finding_refs": [
                    item["title"]
                    for item in key_findings
                    if "signature" in item["title"].lower()
                    or "fusion:" in item["title"]
                ],
                "provenance": provenance(evidence_ids=sig_ids),
            }
        )

    docs = [
        item
        for item in evidence
        if "pdf" in str(item.get("mime_type") or "").lower()
        or "document" in str(item.get("mime_type") or "").lower()
    ]
    if docs:
        recommendations.append(
            {
                "code": RecommendationCode.INTERVIEW_SOURCE.value,
                "title": "Interview document source",
                "rationale": (
                    "Document evidence is present; interviewing the source "
                    "can corroborate provenance and custody."
                ),
                "supporting_finding_refs": [],
                "provenance": provenance(
                    evidence_ids=[str(item["evidence_id"]) for item in docs]
                ),
            }
        )

    missing_meta = any(
        item.get("processing_status") in {"failed", "partial", None}
        for item in evidence
    )
    if missing_meta and evidence:
        recommendations.append(
            {
                "code": RecommendationCode.RECOVER_METADATA.value,
                "title": "Recover deleted metadata",
                "rationale": (
                    "Processing status indicates incomplete metadata "
                    "extraction for one or more evidence items."
                ),
                "supporting_finding_refs": [],
                "provenance": provenance(evidence_ids=evidence_ids),
            }
        )

    audio_or_video = [
        item
        for item in evidence
        if str(item.get("mime_type") or "").startswith(("audio/", "video/"))
    ]
    if audio_or_video:
        recommendations.append(
            {
                "code": RecommendationCode.COLLECT_REFERENCE.value,
                "title": "Collect reference recording",
                "rationale": (
                    "Audio/video evidence benefits from a known-authentic "
                    "reference recording for comparison."
                ),
                "supporting_finding_refs": [],
                "provenance": provenance(
                    evidence_ids=[str(item["evidence_id"]) for item in audio_or_video]
                ),
            }
        )
        recommendations.append(
            {
                "code": RecommendationCode.ACQUIRE_CCTV.value,
                "title": "Acquire CCTV",
                "rationale": (
                    "Supplementary CCTV may contextualize the media timeline."
                ),
                "supporting_finding_refs": [],
                "provenance": provenance(
                    evidence_ids=[str(item["evidence_id"]) for item in audio_or_video]
                ),
            }
        )

    if evidence and not any(
        item.get("coverage_status") == "analyzed" for item in evidence
    ):
        recommendations.append(
            {
                "code": RecommendationCode.ACQUIRE_ORIGINAL.value,
                "title": "Acquire original media",
                "rationale": (
                    "Original-source media should be acquired when only "
                    "derivatives or unanalyzed copies are available."
                ),
                "supporting_finding_refs": [],
                "provenance": provenance(evidence_ids=evidence_ids),
            }
        )

    correlation = snapshot.get("correlation") or {}
    if correlation.get("items"):
        recommendations.append(
            {
                "code": RecommendationCode.REVIEW_CORRELATIONS.value,
                "title": "Review cross-evidence links",
                "rationale": (
                    f"{len(correlation['items'])} correlation(s) were "
                    "detected and should be reviewed for investigative leads."
                ),
                "supporting_finding_refs": [],
                "provenance": provenance(
                    correlation_ids=[str(correlation.get("run_id") or "")],
                    evidence_ids=sorted(
                        {
                            str(item.get("left_evidence_id") or "")
                            for item in correlation["items"]
                        }
                        | {
                            str(item.get("right_evidence_id") or "")
                            for item in correlation["items"]
                        }
                    ),
                ),
            }
        )

    recommendations.append(
        {
            "code": RecommendationCode.EXPORT_REPORT.value,
            "title": "Export report",
            "rationale": (
                "Export a Phase 6H forensic report to preserve a court-ready "
                "snapshot of the current investigation state."
            ),
            "supporting_finding_refs": [item["title"] for item in key_findings[:3]],
            "provenance": provenance(evidence_ids=evidence_ids),
        }
    )

    recommendations.sort(key=lambda row: (row["code"], row["title"]))
    return recommendations
