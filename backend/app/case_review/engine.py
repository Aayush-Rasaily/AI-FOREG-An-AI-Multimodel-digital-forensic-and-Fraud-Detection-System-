"""Case review planner and collection engine."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.case_review.approvals import approval_completion
from backend.app.case_review.checklist import generate_checklist
from backend.app.case_review.models import ReviewPlan, ReviewStage
from backend.app.case_review.policy import CR_ENGINE_VERSION, CR_POLICY_VERSION
from backend.app.case_review.reviewers import required_roles
from backend.app.case_review.scoring import compute_metrics
from backend.app.case_review.validation import evaluate_signals
from backend.app.models.case import Case
from backend.app.models.correlation import EvidenceCorrelationRecord
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.decision_support import (
    DecisionSupportRun,
    DecisionSupportTask,
)
from backend.app.models.document_ai import DocumentAIFinding
from backend.app.models.evidence import Evidence
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.fusion import FusionAnalysisRun, FusionConflictRecord
from backend.app.models.image_ai import ImageAIFinding
from backend.app.models.investigation_intelligence import (
    InvestigationHypothesis,
    InvestigationIntelligenceRun,
    InvestigationRecommendation,
)
from backend.app.models.knowledge_graph import KnowledgeGraphRun
from backend.app.models.timeline import (
    InvestigationTimeline,
    TimelineConflictRecord,
    TimelineEventRecord,
)


def infer_stage(
    *,
    blocking: int,
    outstanding: int,
    approval_pct: float,
    has_rejection: bool,
    has_changes: bool,
    finalized: bool,
) -> ReviewStage:
    if finalized:
        return ReviewStage.FINALIZED
    if has_rejection:
        return ReviewStage.REJECTED
    if has_changes:
        return ReviewStage.CHANGES_REQUESTED
    if approval_pct >= 1.0 and blocking == 0:
        return ReviewStage.APPROVED
    if blocking == 0 and outstanding == 0:
        return ReviewStage.VALIDATED
    if outstanding or blocking:
        return ReviewStage.UNDER_REVIEW
    return ReviewStage.PENDING


def plan_review(
    snapshot: dict[str, Any],
    *,
    approved_roles: set[str] | None = None,
    has_rejection: bool = False,
    has_changes: bool = False,
    finalized: bool = False,
) -> ReviewPlan:
    checklist = generate_checklist(snapshot)
    signals = evaluate_signals(snapshot)
    roles = required_roles()
    approved = approved_roles or set()
    approval_pct = approval_completion(approved, roles)
    metrics = compute_metrics(
        checklist,
        evidence_total=signals["evidence_total"],
        evidence_with_hash=signals["evidence_with_hash"],
        approvals_done=sum(1 for role in roles if role in approved),
        approvals_required=len(roles),
    )
    outstanding = [item.title for item in checklist if item.outstanding]
    blocking = [item.title for item in checklist if item.blocking]
    metrics.outstanding_issues = len(outstanding)
    metrics.blocking_issues = len(blocking)
    metrics.approval_completion_pct = approval_pct
    stage = infer_stage(
        blocking=len(blocking),
        outstanding=len(outstanding),
        approval_pct=approval_pct,
        has_rejection=has_rejection,
        has_changes=has_changes,
        finalized=finalized,
    )
    return ReviewPlan(
        stage=stage,
        checklist=checklist,
        metrics=metrics,
        outstanding=outstanding,
        blocking=blocking,
        required_approver_roles=roles,
        provenance={
            "engine_version": CR_ENGINE_VERSION,
            "policy_version": CR_POLICY_VERSION,
            "sources": sorted(snapshot.get("source_kinds") or []),
            "evidence_count": signals["evidence_total"],
        },
    )


class CaseReviewEngine:
    """Collect existing investigation outputs and plan a case review."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def load_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def plan(
        self,
        case: Case,
        *,
        approved_roles: set[str] | None = None,
        has_rejection: bool = False,
        has_changes: bool = False,
        finalized: bool = False,
    ) -> ReviewPlan:
        snapshot = await self.collect(case.id)
        return plan_review(
            snapshot,
            approved_roles=approved_roles,
            has_rejection=has_rejection,
            has_changes=has_changes,
            finalized=finalized,
        )

    async def collect(self, case_id: UUID) -> dict[str, Any]:
        evidence_result = await self.session.execute(
            select(Evidence).where(Evidence.case_id == case_id)
        )
        evidence_rows = list(evidence_result.scalars().all())
        evidence = [
            {
                "id": str(row.id),
                "sha256_hash": row.sha256_hash,
                "has_metadata": bool(getattr(row, "metadata_json", None) or {}),
            }
            for row in sorted(evidence_rows, key=lambda item: str(item.id))
        ]
        evidence_ids = [UUID(str(item["id"])) for item in evidence]

        custody: dict[str, int] = {}
        if evidence_ids:
            custody_result = await self.session.execute(
                select(
                    ChainOfCustodyEvent.evidence_id,
                    func.count(ChainOfCustodyEvent.id),
                )
                .where(ChainOfCustodyEvent.evidence_id.in_(evidence_ids))
                .group_by(ChainOfCustodyEvent.evidence_id)
            )
            custody = {str(eid): int(count) for eid, count in custody_result.all()}
            for eid in evidence_ids:
                custody.setdefault(str(eid), 0)

        intel_run = (
            (
                await self.session.execute(
                    select(InvestigationIntelligenceRun)
                    .where(InvestigationIntelligenceRun.case_id == case_id)
                    .order_by(InvestigationIntelligenceRun.created_at.desc())
                    .limit(1)
                )
            )
            .scalars()
            .first()
        )
        hypotheses: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []
        if intel_run is not None:
            hyps = await self.session.execute(
                select(InvestigationHypothesis).where(
                    InvestigationHypothesis.run_id == intel_run.id
                )
            )
            hypotheses = [
                {
                    "hypothesis_key": row.hypothesis_key,
                    "hypothesis_type": row.hypothesis_type,
                }
                for row in sorted(
                    hyps.scalars().all(), key=lambda item: item.hypothesis_key
                )
            ]
            recs = await self.session.execute(
                select(InvestigationRecommendation).where(
                    InvestigationRecommendation.run_id == intel_run.id
                )
            )
            recommendations = [
                {"recommendation_key": row.recommendation_key, "code": row.code}
                for row in sorted(
                    recs.scalars().all(),
                    key=lambda item: item.recommendation_key,
                )
            ]

        timeline = (
            (
                await self.session.execute(
                    select(InvestigationTimeline)
                    .where(InvestigationTimeline.case_id == case_id)
                    .order_by(InvestigationTimeline.created_at.desc())
                )
            )
            .scalars()
            .first()
        )
        timeline_events: list[dict[str, Any]] = []
        timeline_conflicts: list[dict[str, Any]] = []
        if timeline is not None:
            events = await self.session.execute(
                select(TimelineEventRecord).where(
                    TimelineEventRecord.timeline_id == timeline.id
                )
            )
            timeline_events = [
                {"id": str(row.id)}
                for row in sorted(events.scalars().all(), key=lambda i: str(i.id))
            ]
            conflicts = await self.session.execute(
                select(TimelineConflictRecord).where(
                    TimelineConflictRecord.timeline_id == timeline.id
                )
            )
            timeline_conflicts = [
                {"id": str(row.id)}
                for row in sorted(conflicts.scalars().all(), key=lambda i: str(i.id))
            ]

        corr = await self.session.execute(
            select(EvidenceCorrelationRecord).where(
                EvidenceCorrelationRecord.case_id == case_id
            )
        )
        correlations = [
            {"id": str(row.id)}
            for row in sorted(corr.scalars().all(), key=lambda i: str(i.id))
        ]

        fusion_runs: list[dict[str, Any]] = []
        fusion_conflicts: list[dict[str, Any]] = []
        if evidence_ids:
            fr = await self.session.execute(
                select(FusionAnalysisRun).where(
                    FusionAnalysisRun.evidence_id.in_(evidence_ids)
                )
            )
            runs = list(fr.scalars().all())
            fusion_runs = [
                {"id": str(row.id), "evidence_id": str(row.evidence_id)}
                for row in sorted(runs, key=lambda i: str(i.id))
            ]
            run_ids = [row.id for row in runs]
            if run_ids:
                fc = await self.session.execute(
                    select(FusionConflictRecord).where(
                        FusionConflictRecord.analysis_run_id.in_(run_ids)
                    )
                )
                fusion_conflicts = [
                    {"id": str(row.id)}
                    for row in sorted(fc.scalars().all(), key=lambda i: str(i.id))
                ]

        ai_findings: list[dict[str, Any]] = []
        if evidence_ids:
            img = await self.session.execute(
                select(ImageAIFinding).where(
                    ImageAIFinding.evidence_id.in_(evidence_ids)
                )
            )
            ai_findings.extend(
                {"id": str(row.id), "evidence_id": str(row.evidence_id)}
                for row in img.scalars().all()
            )
            doc = await self.session.execute(
                select(DocumentAIFinding).where(
                    DocumentAIFinding.evidence_id.in_(evidence_ids)
                )
            )
            ai_findings.extend(
                {"id": str(row.id), "evidence_id": str(row.evidence_id)}
                for row in doc.scalars().all()
            )
            ai_findings = sorted(ai_findings, key=lambda item: item["id"])

        kg = (
            (
                await self.session.execute(
                    select(KnowledgeGraphRun)
                    .where(KnowledgeGraphRun.case_id == case_id)
                    .order_by(KnowledgeGraphRun.created_at.desc())
                    .limit(1)
                )
            )
            .scalars()
            .first()
        )
        knowledge_graph_ids = [str(kg.id)] if kg else []

        ds = (
            (
                await self.session.execute(
                    select(DecisionSupportRun)
                    .where(DecisionSupportRun.case_id == case_id)
                    .order_by(DecisionSupportRun.created_at.desc())
                    .limit(1)
                )
            )
            .scalars()
            .first()
        )
        open_workflow_tasks = 0
        workflow_completion = 0.0
        workflow_task_ids: list[str] = []
        if ds is not None:
            metrics = dict(ds.metrics_json or {})
            open_workflow_tasks = int(metrics.get("open_tasks") or 0)
            workflow_completion = float(metrics.get("workflow_completion") or 0)
            tasks = await self.session.execute(
                select(DecisionSupportTask).where(DecisionSupportTask.run_id == ds.id)
            )
            workflow_task_ids = [
                str(row.id)
                for row in sorted(tasks.scalars().all(), key=lambda i: str(i.id))
            ]

        reports = await self.session.execute(
            select(ForensicReport).where(ForensicReport.case_id == case_id)
        )
        report_rows = [
            {"id": str(row.id)}
            for row in sorted(reports.scalars().all(), key=lambda i: str(i.id))
        ]

        source_kinds = {"case", "evidence"}
        if hypotheses:
            source_kinds.add("investigation_intelligence")
        if ds is not None:
            source_kinds.add("decision_support")
        if timeline_events:
            source_kinds.add("timeline")
        if correlations:
            source_kinds.add("correlation")
        if fusion_runs:
            source_kinds.add("fusion")
        if knowledge_graph_ids:
            source_kinds.add("knowledge_graph")
        if report_rows:
            source_kinds.add("report")
        if ai_findings:
            source_kinds.add("ai_findings")

        return {
            "evidence": evidence,
            "custody_by_evidence": custody,
            "hypotheses": hypotheses,
            "recommendations": recommendations,
            "timeline_events": timeline_events,
            "timeline_conflicts": timeline_conflicts,
            "correlations": correlations,
            "fusion_runs": fusion_runs,
            "fusion_conflicts": fusion_conflicts,
            "ai_findings": ai_findings,
            "knowledge_graph_ids": knowledge_graph_ids,
            "reports": report_rows,
            "open_workflow_tasks": open_workflow_tasks,
            "workflow_completion": workflow_completion,
            "workflow_task_ids": workflow_task_ids,
            "open_conflicts": [
                *[
                    {"kind": "timeline", "id": item["id"]}
                    for item in timeline_conflicts
                ],
                *[{"kind": "fusion", "id": item["id"]} for item in fusion_conflicts],
            ],
            "source_kinds": list(source_kinds),
        }
