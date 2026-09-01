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
        intelligence = snapshot.get("case_intelligence") or {}
        return ReportResult(
            status=ReportStatus.COMPLETED,
            content=content,
            provenance={
                "case_id": str(case.id),
                "case_number": case.case_number,
                "report_version": REPORT_VERSION,
                "engine_version": ENGINE_VERSION,
                "evidence_hashes": snapshot.get("evidence_hashes", []),
                "case_intelligence_run_id": intelligence.get("analysis_run_id"),
                "fusion_run_ids": [
                    item["fusion_run_id"]
                    for item in snapshot.get("fusion_snapshots", [])
                ],
                "generated_at": generated_at,
            },
            metadata={
                "evidence_count": len(snapshot.get("evidence", [])),
                "fusion_count": len(snapshot.get("fusion_snapshots", [])),
                "has_case_intelligence": bool(snapshot.get("case_intelligence")),
            },
        )
