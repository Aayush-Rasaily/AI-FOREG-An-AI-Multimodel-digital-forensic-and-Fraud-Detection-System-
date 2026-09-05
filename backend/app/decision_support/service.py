"""Service facade for Phase 9D decision support."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.decision_support.decision_log import normalize_decision_type
from backend.app.decision_support.engine import DecisionSupportEngine
from backend.app.decision_support.exceptions import (
    DecisionSupportError,
    WorkflowRunNotFoundError,
    WorkflowTaskNotFoundError,
)
from backend.app.decision_support.models import RunStatus, WorkflowPlan, WorkloadMetrics
from backend.app.decision_support.policy import DS_ENGINE_VERSION, DS_POLICY_VERSION
from backend.app.decision_support.provenance import provenance_to_dict
from backend.app.decision_support.repository import DecisionSupportRepository
from backend.app.decision_support.schemas import (
    DecisionCreateRequest,
    DecisionLogListResponse,
    DecisionLogResponse,
    ReviewQueueItemResponse,
    ReviewQueueListResponse,
    TaskUpdateRequest,
    WorkflowPreviewResponse,
    WorkflowRunResponse,
    WorkflowTaskListResponse,
    WorkflowTaskResponse,
    WorkloadMetricsResponse,
)
from backend.app.models.decision_support import (
    DecisionSupportDecision,
    DecisionSupportReviewItem,
    DecisionSupportRun,
    DecisionSupportTask,
)


class DecisionSupportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = DecisionSupportRepository(session)
        self.engine = DecisionSupportEngine(session)

    def _metrics(self, data: dict | WorkloadMetrics) -> WorkloadMetricsResponse:
        if isinstance(data, dict):
            return WorkloadMetricsResponse(**data)
        return WorkloadMetricsResponse(
            open_tasks=data.open_tasks,
            completed_tasks=data.completed_tasks,
            pending_reviews=data.pending_reviews,
            average_priority=data.average_priority,
            critical_evidence_count=data.critical_evidence_count,
            workflow_completion=data.workflow_completion,
            investigation_progress=data.investigation_progress,
            evidence_review_coverage=data.evidence_review_coverage,
        )

    def _task_response(self, row: DecisionSupportTask) -> WorkflowTaskResponse:
        return WorkflowTaskResponse(
            id=row.id,
            run_id=row.run_id,
            case_id=row.case_id,
            task_key=row.task_key,
            task_type=row.task_type,
            stage=row.stage,
            title=row.title,
            description=row.description,
            priority=row.priority,
            status=row.status,
            estimated_effort_hours=row.estimated_effort_hours,
            priority_score=row.priority_score,
            required_evidence_ids=list(row.required_evidence_ids_json or []),
            supporting_intelligence=dict(
                row.supporting_intelligence_json or {}
            ),
            provenance=dict(row.provenance_json or {}),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _review_response(
        self, row: DecisionSupportReviewItem,
    ) -> ReviewQueueItemResponse:
        return ReviewQueueItemResponse(
            id=row.id,
            run_id=row.run_id,
            case_id=row.case_id,
            queue_key=row.queue_key,
            evidence_id=row.evidence_id,
            priority=row.priority,
            priority_score=row.priority_score,
            reasons=list(row.reasons_json or []),
            provenance=dict(row.provenance_json or {}),
        )

    def _plan_to_drafts(
        self, case_id: UUID, plan: WorkflowPlan,
    ) -> tuple[list[WorkflowTaskResponse], list[ReviewQueueItemResponse]]:
        tasks = [
            WorkflowTaskResponse(
                case_id=case_id,
                task_key=item.task_key,
                task_type=item.task_type.value,
                stage=item.stage.value,
                title=item.title,
                description=item.description,
                priority=item.priority.value,
                status=item.status.value,
                estimated_effort_hours=item.estimated_effort_hours,
                priority_score=item.priority_score,
                required_evidence_ids=item.required_evidence_ids,
                supporting_intelligence=item.supporting_intelligence,
                provenance=provenance_to_dict(item.provenance),
            )
            for item in plan.tasks
        ]
        reviews = [
            ReviewQueueItemResponse(
                case_id=case_id,
                queue_key=item.queue_key,
                evidence_id=item.evidence_id,
                priority=item.priority.value,
                priority_score=item.priority_score,
                reasons=item.reasons,
                provenance=provenance_to_dict(item.provenance),
            )
            for item in plan.review_queue
        ]
        return tasks, reviews

    async def _hydrate(self, run: DecisionSupportRun) -> WorkflowRunResponse:
        tasks = [
            self._task_response(row)
            for row in await self.repository.tasks_for_run(run.id)
        ]
        reviews = [
            self._review_response(row)
            for row in await self.repository.reviews_for_run(run.id)
        ]
        return WorkflowRunResponse(
            id=run.id,
            case_id=run.case_id,
            status=run.status,
            current_stage=run.current_stage,
            task_count=run.task_count,
            review_count=run.review_count,
            metrics=self._metrics(run.metrics_json or {}),
            open_conflicts=list(run.open_conflicts_json or []),
            provenance=dict(run.provenance_json or {}),
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            created_at=run.created_at,
            completed_at=run.completed_at,
            tasks=tasks,
            review_queue=reviews,
            persisted=True,
        )

    async def generate(self, case_id: UUID) -> WorkflowRunResponse:
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        plan = await self.engine.plan(case)
        run = DecisionSupportRun(
            case_id=case_id,
            status=RunStatus.SUCCEEDED.value,
            current_stage=plan.current_stage.value,
            task_count=len(plan.tasks),
            review_count=len(plan.review_queue),
            metrics_json=self._metrics(plan.metrics).model_dump(),
            open_conflicts_json=plan.open_conflicts,
            provenance_json=plan.provenance,
            engine_version=DS_ENGINE_VERSION,
            policy_version=DS_POLICY_VERSION,
            completed_at=datetime.now(UTC),
        )
        await self.repository.add_run(run)
        task_rows = [
            DecisionSupportTask(
                run_id=run.id,
                case_id=case_id,
                task_key=item.task_key,
                task_type=item.task_type.value,
                stage=item.stage.value,
                title=item.title,
                description=item.description,
                priority=item.priority.value,
                status=item.status.value,
                estimated_effort_hours=item.estimated_effort_hours,
                priority_score=item.priority_score,
                required_evidence_ids_json=item.required_evidence_ids,
                supporting_intelligence_json=item.supporting_intelligence,
                provenance_json=provenance_to_dict(item.provenance),
            )
            for item in plan.tasks
        ]
        review_rows = [
            DecisionSupportReviewItem(
                run_id=run.id,
                case_id=case_id,
                queue_key=item.queue_key,
                evidence_id=item.evidence_id,
                priority=item.priority.value,
                priority_score=item.priority_score,
                reasons_json=item.reasons,
                provenance_json=provenance_to_dict(item.provenance),
            )
            for item in plan.review_queue
        ]
        await self.repository.add_tasks(task_rows)
        await self.repository.add_reviews(review_rows)
        await self.session.commit()
        await self.session.refresh(run)
        return await self._hydrate(run)

    async def preview(self, case_id: UUID) -> WorkflowPreviewResponse:
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        plan = await self.engine.plan(case)
        tasks, reviews = self._plan_to_drafts(case_id, plan)
        return WorkflowPreviewResponse(
            case_id=case_id,
            status=RunStatus.SUCCEEDED.value,
            current_stage=plan.current_stage.value,
            task_count=len(tasks),
            review_count=len(reviews),
            metrics=self._metrics(plan.metrics),
            open_conflicts=plan.open_conflicts,
            provenance=plan.provenance,
            engine_version=DS_ENGINE_VERSION,
            policy_version=DS_POLICY_VERSION,
            tasks=tasks,
            review_queue=reviews,
            persisted=False,
        )

    async def get_latest(self, case_id: UUID) -> WorkflowRunResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            raise WorkflowRunNotFoundError(
                "No decision-support workflow for this case."
            )
        return await self._hydrate(run)

    async def get_run(self, run_id: UUID) -> WorkflowRunResponse:
        run = await self.repository.get_run(run_id)
        if run is None:
            raise WorkflowRunNotFoundError("Decision-support run not found.")
        return await self._hydrate(run)

    async def list_tasks(
        self, case_id: UUID,
    ) -> WorkflowTaskListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            return WorkflowTaskListResponse(items=[], total=0)
        rows = await self.repository.tasks_for_run(run.id)
        return WorkflowTaskListResponse(
            items=[self._task_response(row) for row in rows],
            total=len(rows),
        )

    async def update_task(
        self, task_id: UUID, payload: TaskUpdateRequest,
    ) -> WorkflowTaskResponse:
        task = await self.repository.get_task(task_id)
        if task is None:
            raise WorkflowTaskNotFoundError("Workflow task not found.")
        if payload.status is not None:
            allowed = {
                "OPEN",
                "IN_PROGRESS",
                "BLOCKED",
                "COMPLETED",
                "CANCELLED",
            }
            status = payload.status.strip().upper()
            if status not in allowed:
                raise DecisionSupportError(f"Invalid task status: {payload.status}")
            task.status = status
        if payload.priority is not None:
            priority = payload.priority.strip().upper()
            if priority not in {"HIGH", "MEDIUM", "LOW"}:
                raise DecisionSupportError(
                    f"Invalid task priority: {payload.priority}"
                )
            task.priority = priority
        task.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(task)
        return self._task_response(task)

    async def list_review_queue(
        self, case_id: UUID,
    ) -> ReviewQueueListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            return ReviewQueueListResponse(items=[], total=0)
        rows = await self.repository.reviews_for_run(run.id)
        return ReviewQueueListResponse(
            items=[self._review_response(row) for row in rows],
            total=len(rows),
        )

    async def record_decision(
        self, payload: DecisionCreateRequest,
    ) -> DecisionLogResponse:
        if await self.repository.get_case(payload.case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        try:
            decision_type = normalize_decision_type(payload.decision_type)
        except ValueError as exc:
            raise DecisionSupportError(str(exc)) from exc
        if payload.task_id is not None:
            task = await self.repository.get_task(payload.task_id)
            if task is None:
                raise WorkflowTaskNotFoundError("Workflow task not found.")
        run_id = payload.run_id
        if run_id is None:
            latest = await self.repository.get_latest_run(payload.case_id)
            run_id = latest.id if latest else None
        row = DecisionSupportDecision(
            case_id=payload.case_id,
            run_id=run_id,
            task_id=payload.task_id,
            decision_type=decision_type,
            investigator=payload.investigator.strip() or "unknown",
            justification=payload.justification.strip(),
            provenance_json={
                **dict(payload.provenance or {}),
                "engine_version": DS_ENGINE_VERSION,
                "policy_version": DS_POLICY_VERSION,
            },
        )
        await self.repository.add_decision(row)
        await self.session.commit()
        await self.session.refresh(row)
        return DecisionLogResponse(
            id=row.id,
            case_id=row.case_id,
            run_id=row.run_id,
            task_id=row.task_id,
            decision_type=row.decision_type,
            investigator=row.investigator,
            justification=row.justification,
            provenance=dict(row.provenance_json or {}),
            created_at=row.created_at,
        )

    async def list_decisions(
        self, case_id: UUID, *, limit: int = 100, offset: int = 0,
    ) -> DecisionLogListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        rows, total = await self.repository.list_decisions(
            case_id, limit=limit, offset=offset,
        )
        return DecisionLogListResponse(
            items=[
                DecisionLogResponse(
                    id=row.id,
                    case_id=row.case_id,
                    run_id=row.run_id,
                    task_id=row.task_id,
                    decision_type=row.decision_type,
                    investigator=row.investigator,
                    justification=row.justification,
                    provenance=dict(row.provenance_json or {}),
                    created_at=row.created_at,
                )
                for row in rows
            ],
            total=total,
        )

    async def metrics(self, case_id: UUID) -> WorkloadMetricsResponse:
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            # Live preview metrics without persist
            preview = await self.preview(case_id)
            return preview.metrics
        return self._metrics(run.metrics_json or {})
