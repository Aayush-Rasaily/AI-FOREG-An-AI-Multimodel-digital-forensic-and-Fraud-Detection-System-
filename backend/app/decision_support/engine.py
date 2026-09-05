"""Decision support engine — collect case outputs and plan workflows."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.decision_support.models import WorkflowPlan
from backend.app.decision_support.planner import plan_workflow
from backend.app.models.case import Case
from backend.app.models.correlation import EvidenceCorrelationRecord
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.evidence import Evidence
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.fusion import FusionAnalysisRun, FusionConflictRecord
from backend.app.models.investigation_intelligence import (
    EvidenceGapRecordRow,
    InvestigationHypothesis,
    InvestigationIntelligenceRun,
    InvestigationRecommendation,
)
from backend.app.models.knowledge_graph import KnowledgeGraphRun
from backend.app.models.timeline import (
    InvestigationTimeline,
    TimelineConflictRecord,
)


class DecisionSupportEngine:
    """Build investigator workflows from existing investigation outputs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def load_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def plan(self, case: Case) -> WorkflowPlan:
        snapshot = await self.collect(case.id)
        return plan_workflow(snapshot)

    async def collect(self, case_id: UUID) -> dict[str, Any]:
        evidence = await self._evidence(case_id)
        evidence_ids = [UUID(item["id"]) for item in evidence]
        intelligence = await self._intelligence(case_id)
        correlations = await self._correlations(case_id)
        fusion_runs, fusion_conflicts = await self._fusion(evidence_ids)
        timeline_conflicts = await self._timeline_conflicts(case_id)
        custody = await self._custody(evidence_ids)
        reports = await self._reports(case_id)
        kg = await self._knowledge_graph(case_id)

        open_conflicts: list[dict[str, Any]] = []
        for item in timeline_conflicts:
            open_conflicts.append(
                {
                    "kind": "timeline",
                    "id": item["id"],
                    "evidence_ids": item.get("evidence_ids") or [],
                }
            )
        for item in fusion_conflicts:
            open_conflicts.append(
                {
                    "kind": "fusion",
                    "id": item["id"],
                    "detail": item.get("conflict_type"),
                }
            )

        source_kinds = {"case", "evidence"}
        if intelligence.get("hypotheses") or intelligence.get("gaps"):
            source_kinds.add("investigation_intelligence")
        if correlations:
            source_kinds.add("correlation")
        if fusion_runs:
            source_kinds.add("fusion")
        if timeline_conflicts:
            source_kinds.add("timeline")
        if kg:
            source_kinds.add("knowledge_graph")
        if reports:
            source_kinds.add("report")

        return {
            "evidence": evidence,
            "hypotheses": intelligence.get("hypotheses") or [],
            "gaps": intelligence.get("gaps") or [],
            "recommendations": intelligence.get("recommendations") or [],
            "coverage": intelligence.get("coverage") or {
                "evidence_total": len(evidence),
                "overall_completeness": 0.0,
            },
            "correlations": correlations,
            "fusion_runs": fusion_runs,
            "open_conflicts": open_conflicts,
            "custody_by_evidence": custody,
            "reports": reports,
            "knowledge_graph_ids": kg,
            "source_kinds": list(source_kinds),
        }

    async def _evidence(self, case_id: UUID) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(Evidence).where(Evidence.case_id == case_id)
        )
        rows = list(result.scalars().all())
        out: list[dict[str, Any]] = []
        for row in sorted(rows, key=lambda item: str(item.id)):
            meta = getattr(row, "metadata_json", None) or {}
            out.append(
                {
                    "id": str(row.id),
                    "mime_type": row.mime_type,
                    "has_metadata": bool(meta),
                }
            )
        return out

    async def _intelligence(self, case_id: UUID) -> dict[str, Any]:
        run_result = await self.session.execute(
            select(InvestigationIntelligenceRun)
            .where(InvestigationIntelligenceRun.case_id == case_id)
            .order_by(InvestigationIntelligenceRun.created_at.desc())
            .limit(1)
        )
        run = run_result.scalars().first()
        if run is None:
            return {}
        hyps = await self.session.execute(
            select(InvestigationHypothesis).where(
                InvestigationHypothesis.run_id == run.id
            )
        )
        gaps = await self.session.execute(
            select(EvidenceGapRecordRow).where(
                EvidenceGapRecordRow.run_id == run.id
            )
        )
        recs = await self.session.execute(
            select(InvestigationRecommendation).where(
                InvestigationRecommendation.run_id == run.id
            )
        )
        return {
            "coverage": dict(run.coverage_json or {}),
            "hypotheses": [
                {
                    "hypothesis_key": row.hypothesis_key,
                    "hypothesis_type": row.hypothesis_type,
                    "explanation": row.explanation,
                    "supporting_evidence_ids": list(
                        row.supporting_evidence_ids_json or []
                    ),
                    "provenance": dict(row.provenance_json or {}),
                }
                for row in sorted(
                    hyps.scalars().all(), key=lambda item: item.hypothesis_key
                )
            ],
            "gaps": [
                {
                    "gap_key": row.gap_key,
                    "gap_type": row.gap_type,
                    "severity": row.severity,
                    "reason": row.reason,
                    "affected_evidence_ids": list(
                        row.affected_evidence_ids_json or []
                    ),
                }
                for row in sorted(
                    gaps.scalars().all(), key=lambda item: item.gap_key
                )
            ],
            "recommendations": [
                {
                    "recommendation_key": row.recommendation_key,
                    "code": row.code,
                    "action_text": row.action_text,
                    "priority": row.priority,
                    "affected_evidence_ids": list(
                        row.affected_evidence_ids_json or []
                    ),
                }
                for row in sorted(
                    recs.scalars().all(), key=lambda item: item.recommendation_key
                )
            ],
        }

    async def _correlations(self, case_id: UUID) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(EvidenceCorrelationRecord).where(
                EvidenceCorrelationRecord.case_id == case_id
            )
        )
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "left_evidence_id": str(row.left_evidence_id),
                "right_evidence_id": str(
                    getattr(row, "right_evidence_id", None) or ""
                ),
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _fusion(
        self, evidence_ids: list[UUID],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not evidence_ids:
            return [], []
        runs_result = await self.session.execute(
            select(FusionAnalysisRun).where(
                FusionAnalysisRun.evidence_id.in_(evidence_ids)
            )
        )
        runs = list(runs_result.scalars().all())
        run_rows = [
            {
                "id": str(row.id),
                "evidence_id": str(row.evidence_id),
                "confidence": float(row.confidence or 0),
                "risk_score": float(row.risk_score or 0),
            }
            for row in sorted(runs, key=lambda item: str(item.id))
        ]
        run_ids = [row.id for row in runs]
        conflicts: list[dict[str, Any]] = []
        if run_ids:
            conf_result = await self.session.execute(
                select(FusionConflictRecord).where(
                    FusionConflictRecord.analysis_run_id.in_(run_ids)
                )
            )
            conflicts = [
                {
                    "id": str(row.id),
                    "conflict_type": str(getattr(row, "conflict_type", "")),
                }
                for row in sorted(
                    conf_result.scalars().all(), key=lambda item: str(item.id)
                )
            ]
        return run_rows, conflicts

    async def _timeline_conflicts(
        self, case_id: UUID,
    ) -> list[dict[str, Any]]:
        tl = await self.session.execute(
            select(InvestigationTimeline)
            .where(InvestigationTimeline.case_id == case_id)
            .order_by(InvestigationTimeline.created_at.desc())
        )
        timeline = tl.scalars().first()
        if timeline is None:
            return []
        result = await self.session.execute(
            select(TimelineConflictRecord).where(
                TimelineConflictRecord.timeline_id == timeline.id
            )
        )
        return [
            {
                "id": str(row.id),
                "evidence_ids": (
                    [str(row.evidence_id)] if row.evidence_id else []
                ),
            }
            for row in sorted(result.scalars().all(), key=lambda item: str(item.id))
        ]

    async def _custody(self, evidence_ids: list[UUID]) -> dict[str, int]:
        if not evidence_ids:
            return {}
        result = await self.session.execute(
            select(
                ChainOfCustodyEvent.evidence_id,
                func.count(ChainOfCustodyEvent.id),
            )
            .where(ChainOfCustodyEvent.evidence_id.in_(evidence_ids))
            .group_by(ChainOfCustodyEvent.evidence_id)
        )
        counts = {str(eid): int(count) for eid, count in result.all()}
        for eid in evidence_ids:
            counts.setdefault(str(eid), 0)
        return counts

    async def _reports(self, case_id: UUID) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(ForensicReport).where(ForensicReport.case_id == case_id)
        )
        return [
            {"id": str(row.id)}
            for row in sorted(result.scalars().all(), key=lambda item: str(item.id))
        ]

    async def _knowledge_graph(self, case_id: UUID) -> list[str]:
        result = await self.session.execute(
            select(KnowledgeGraphRun)
            .where(KnowledgeGraphRun.case_id == case_id)
            .order_by(KnowledgeGraphRun.created_at.desc())
            .limit(1)
        )
        run = result.scalars().first()
        return [str(run.id)] if run else []
