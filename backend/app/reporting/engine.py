"""Report generation engine."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.case import Case
from backend.app.reporting.aggregation import aggregate_report_data
from backend.app.reporting.builder import build_report_content
from backend.app.reporting.models import ReportResult, ReportStatus
from backend.app.reporting.policy import ENGINE_VERSION, REPORT_VERSION
from backend.app.reporting.provenance import build_report_provenance


class ReportEngine:
    """Orchestrate deterministic forensic report generation."""

    async def generate(
        self,
        session: AsyncSession,
        *,
        case: Case,
        report_id: UUID,
    ) -> ReportResult:
        snapshot = await aggregate_report_data(session, case)
        generated_at = datetime.now(UTC).isoformat()
        content = build_report_content(
            report_id=str(report_id),
            generated_at=generated_at,
            snapshot=snapshot,
        )
        checksum = content.get("report_checksum", "")

        intelligence = snapshot.get("case_intelligence") or {}
        correlation = snapshot.get("correlation") or {}
        entity_res = snapshot.get("entity_resolution") or {}
        timeline = snapshot.get("timeline") or {}

        included_ids = {
            "case_intelligence_run_id": (
                intelligence.get("analysis_run_id")
            ),
            "fusion_run_ids": [
                item["fusion_run_id"]
                for item in snapshot.get("fusion_snapshots", [])
            ],
            "correlation_run_id": correlation.get("run_id"),
            "entity_resolution_run_id": entity_res.get("run_id"),
            "timeline_run_id": timeline.get("run_id"),
        }

        policy_versions = {
            "fusion": sorted(
                {
                    item["policy_version"]
                    for item in snapshot.get("fusion_snapshots", [])
                    if item.get("policy_version")
                }
            ),
            "case_intelligence": (
                intelligence.get("policy_version")
            ),
            "correlation": correlation.get("policy_version"),
        }

        provenance = build_report_provenance(
            case_id=str(case.id),
            case_number=case.case_number,
            evidence_hashes=snapshot.get("evidence_hashes", []),
            included_analysis_run_ids=included_ids,
            engine_version=ENGINE_VERSION,
            report_version=REPORT_VERSION,
            policy_versions=policy_versions,
            checksum=checksum,
        )

        return ReportResult(
            status=ReportStatus.COMPLETED,
            content=content,
            provenance=provenance,
            metadata={
                "evidence_count": len(snapshot.get("evidence", [])),
                "fusion_count": len(
                    snapshot.get("fusion_snapshots", []),
                ),
                "has_case_intelligence": bool(
                    snapshot.get("case_intelligence"),
                ),
                "has_correlation": bool(
                    snapshot.get("correlation"),
                ),
                "has_entity_resolution": bool(
                    snapshot.get("entity_resolution"),
                ),
                "has_timeline": bool(
                    snapshot.get("timeline"),
                ),
                "report_checksum": checksum,
                "included_analysis_run_ids": included_ids,
            },
        )
