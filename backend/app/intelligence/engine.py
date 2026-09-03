"""Investigation intelligence engine pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.intelligence.confidence import compute_overall_confidence
from backend.app.intelligence.findings import (
    compute_overall_risk,
    extract_key_findings,
)
from backend.app.intelligence.models import ENGINE_VERSION, POLICY_VERSION
from backend.app.intelligence.narrative import generate_narrative
from backend.app.intelligence.provenance import collect_snapshot_provenance
from backend.app.intelligence.recommendations import generate_recommendations
from backend.app.intelligence.summarizer import (
    summarize_ai,
    summarize_correlations,
    summarize_overview,
    summarize_timeline,
)
from backend.app.models.case import Case
from backend.app.models.investigation_summary import InvestigationSummary
from backend.app.reporting.aggregation import aggregate_report_data


class InvestigationIntelligenceEngine:
    """Deterministic pipeline: collect → summarize → narrative → persist."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def collect(self, case: Case) -> dict[str, Any]:
        """Read only persisted analysis outputs for the case."""

        return await aggregate_report_data(self.session, case)

    def normalize(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Return a stably ordered snapshot for deterministic processing."""

        evidence = sorted(
            list(snapshot.get("evidence", [])),
            key=lambda row: (
                str(row.get("evidence_number") or ""),
                str(row.get("evidence_id") or ""),
            ),
        )
        fusion = sorted(
            list(snapshot.get("fusion_snapshots", [])),
            key=lambda row: (
                str(row.get("evidence_number") or ""),
                str(row.get("fusion_run_id") or ""),
            ),
        )
        analyses = sorted(
            list(snapshot.get("analysis_summaries", [])),
            key=lambda row: (
                str(row.get("evidence_number") or ""),
                str(row.get("evidence_id") or ""),
            ),
        )
        normalized = dict(snapshot)
        normalized["evidence"] = evidence
        normalized["fusion_snapshots"] = fusion
        normalized["analysis_summaries"] = analyses
        return normalized

    def build(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Run prioritize → summarize → narrative → recommendations."""

        key_findings = extract_key_findings(snapshot)
        overview = summarize_overview(snapshot)
        timeline_summary = summarize_timeline(snapshot)
        correlation_summary = summarize_correlations(snapshot)
        ai_summary = summarize_ai(snapshot)
        confidence = compute_overall_confidence(snapshot)
        risk = compute_overall_risk(snapshot, key_findings)
        recommendations = generate_recommendations(snapshot, key_findings)
        narrative = generate_narrative(
            overview=overview,
            key_findings=key_findings,
            timeline_summary=timeline_summary,
            correlation_summary=correlation_summary,
            ai_summary=ai_summary,
            overall_risk=risk.value,
            overall_confidence=int(confidence["overall_confidence"]),
            recommendations=recommendations,
        )
        return {
            "overall_risk": risk.value,
            "overall_confidence": int(confidence["overall_confidence"]),
            "confidence_factors": confidence["factors"],
            "overview": overview,
            "key_findings": key_findings,
            "timeline_summary": timeline_summary,
            "correlation_summary": correlation_summary,
            "ai_summary": ai_summary,
            "recommendations": recommendations,
            "narrative": narrative,
            "provenance": {
                "snapshot": collect_snapshot_provenance(snapshot),
                "confidence_factors": confidence["factors"],
            },
            "engine_version": ENGINE_VERSION,
            "policy_version": POLICY_VERSION,
        }

    def to_orm(
        self,
        *,
        case_id: UUID,
        payload: dict[str, Any],
    ) -> InvestigationSummary:
        """Map an engine payload to a persistence row."""

        return InvestigationSummary(
            case_id=case_id,
            generated_at=datetime.now(UTC),
            overall_risk=str(payload["overall_risk"]),
            overall_confidence=int(payload["overall_confidence"]),
            overview_json=payload["overview"],
            key_findings_json=payload["key_findings"],
            timeline_summary_json=payload["timeline_summary"],
            correlation_summary_json=payload["correlation_summary"],
            ai_summary_json=payload["ai_summary"],
            recommendations_json=payload["recommendations"],
            provenance_json=payload["provenance"],
            narrative_json=payload["narrative"],
            engine_version=str(payload["engine_version"]),
            policy_version=str(payload["policy_version"]),
        )
