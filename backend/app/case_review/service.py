"""Service facade for Phase 9E case review."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.case_review.approvals import normalize_approval_decision
from backend.app.case_review.engine import CaseReviewEngine, plan_review
from backend.app.case_review.exceptions import (
    CaseReviewError,
    CaseReviewNotFoundError,
    ChecklistItemNotFoundError,
)
from backend.app.case_review.models import ChecklistItemStatus, RunStatus
from backend.app.case_review.policy import CR_ENGINE_VERSION, CR_POLICY_VERSION
from backend.app.case_review.provenance import provenance_to_dict
from backend.app.case_review.repository import CaseReviewRepository
from backend.app.case_review.reviewers import normalize_approver_role
from backend.app.case_review.schemas import (
    ApprovalCreateRequest,
    ApprovalListResponse,
    ApprovalResponse,
    CaseReviewHistoryItem,
    CaseReviewHistoryResponse,
    CaseReviewPreviewResponse,
    CaseReviewRunResponse,
    ChecklistItemResponse,
    ChecklistItemUpdateRequest,
    ChecklistListResponse,
    ValidationMetricsResponse,
)
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.models.case_review import (
    CaseReviewApproval,
    CaseReviewChecklist,
    CaseReviewChecklistItem,
    CaseReviewRun,
    CaseReviewValidationRecord,
)


class CaseReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CaseReviewRepository(session)
        self.engine = CaseReviewEngine(session)

    def _metrics(self, data: dict | object) -> ValidationMetricsResponse:
        if isinstance(data, dict):
            return ValidationMetricsResponse(**data)
        return ValidationMetricsResponse(
            validation_pct=getattr(data, "validation_pct", 0.0),
            evidence_coverage_pct=getattr(data, "evidence_coverage_pct", 0.0),
            review_completion_pct=getattr(data, "review_completion_pct", 0.0),
            approval_completion_pct=getattr(
                data,
                "approval_completion_pct",
                0.0,
            ),
            outstanding_issues=getattr(data, "outstanding_issues", 0),
            blocking_issues=getattr(data, "blocking_issues", 0),
        )

    def _item_response(
        self,
        row: CaseReviewChecklistItem,
    ) -> ChecklistItemResponse:
        return ChecklistItemResponse(
            id=row.id,
            checklist_id=row.checklist_id,
            run_id=row.run_id,
            case_id=row.case_id,
            item_key=row.item_key,
            item_code=row.item_code,
            title=row.title,
            status=row.status,
            suggested_status=row.suggested_status,
            blocking=row.blocking,
            outstanding=row.outstanding,
            notes=row.notes,
            reviewer=row.reviewer,
            reviewed_at=row.reviewed_at,
            provenance=dict(row.provenance_json or {}),
            created_at=row.created_at,
        )

    def _approval_response(self, row: CaseReviewApproval) -> ApprovalResponse:
        return ApprovalResponse(
            id=row.id,
            run_id=row.run_id,
            case_id=row.case_id,
            checklist_id=row.checklist_id,
            checklist_item_id=row.checklist_item_id,
            reviewer=row.reviewer,
            approver_role=row.approver_role,
            decision=row.decision,
            comments=row.comments,
            provenance=dict(row.provenance_json or {}),
            created_at=row.created_at,
        )

    def _plan_to_drafts(
        self,
        case_id: UUID,
        plan: object,
    ) -> list[ChecklistItemResponse]:
        return [
            ChecklistItemResponse(
                case_id=case_id,
                item_key=item.item_key,
                item_code=item.item_code,
                title=item.title,
                status=item.status.value,
                suggested_status=item.suggested_status.value,
                blocking=item.blocking,
                outstanding=item.outstanding,
                notes=item.notes,
                provenance=provenance_to_dict(item.provenance),
            )
            for item in plan.checklist  # type: ignore[attr-defined]
        ]

    async def _recompute_stage(self, run: CaseReviewRun) -> None:
        items = await self.repository.items_for_run(run.id)
        approvals = await self.repository.approvals_for_run(run.id)
        approved = {
            row.approver_role for row in approvals if row.decision == "APPROVED"
        }
        has_rejection = any(row.decision == "REJECTED" for row in approvals)
        has_changes = any(row.decision == "CHANGES_REQUESTED" for row in approvals)
        live = await self.engine.collect(run.case_id)
        plan = plan_review(
            live,
            approved_roles=approved,
            has_rejection=has_rejection,
            has_changes=has_changes,
            finalized=run.stage == "FINALIZED",
        )
        # Override outstanding/blocking from persisted item flags
        outstanding = [item.title for item in items if item.outstanding]
        blocking = [item.title for item in items if item.blocking]
        plan.metrics.outstanding_issues = len(outstanding)
        plan.metrics.blocking_issues = len(blocking)
        # Recompute review completion from actual statuses
        total = len(items) or 1
        passed = sum(1 for item in items if item.status in {"PASS", "NA"})
        reviewed = sum(1 for item in items if item.status != "PENDING")
        plan.metrics.validation_pct = round(passed / total, 4)
        plan.metrics.review_completion_pct = round(reviewed / total, 4)
        run.stage = plan.stage.value
        run.metrics_json = self._metrics(plan.metrics).model_dump()
        run.outstanding_json = outstanding
        run.blocking_json = blocking
        run.approval_count = len(approvals)

    async def _hydrate(self, run: CaseReviewRun) -> CaseReviewRunResponse:
        items = [
            self._item_response(row)
            for row in await self.repository.items_for_run(run.id)
        ]
        approvals = [
            self._approval_response(row)
            for row in await self.repository.approvals_for_run(run.id)
        ]
        return CaseReviewRunResponse(
            id=run.id,
            case_id=run.case_id,
            status=run.status,
            stage=run.stage,
            checklist_count=run.checklist_count,
            approval_count=run.approval_count,
            metrics=self._metrics(run.metrics_json or {}),
            outstanding=list(run.outstanding_json or []),
            blocking=list(run.blocking_json or []),
            required_roles=list(run.required_roles_json or []),
            provenance=dict(run.provenance_json or {}),
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            created_at=run.created_at,
            completed_at=run.completed_at,
            checklist=items,
            approvals=approvals,
            persisted=True,
        )

    async def generate(self, case_id: UUID) -> CaseReviewRunResponse:
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        plan = await self.engine.plan(case)
        run = CaseReviewRun(
            case_id=case_id,
            status=RunStatus.SUCCEEDED.value,
            stage=plan.stage.value,
            checklist_count=len(plan.checklist),
            approval_count=0,
            metrics_json=self._metrics(plan.metrics).model_dump(),
            outstanding_json=plan.outstanding,
            blocking_json=plan.blocking,
            required_roles_json=plan.required_approver_roles,
            provenance_json=plan.provenance,
            engine_version=CR_ENGINE_VERSION,
            policy_version=CR_POLICY_VERSION,
            completed_at=datetime.now(UTC),
        )
        await self.repository.add_run(run)
        checklist = CaseReviewChecklist(
            run_id=run.id,
            case_id=case_id,
            item_count=len(plan.checklist),
        )
        await self.repository.add_checklist(checklist)
        item_rows = [
            CaseReviewChecklistItem(
                checklist_id=checklist.id,
                run_id=run.id,
                case_id=case_id,
                item_key=item.item_key,
                item_code=item.item_code,
                title=item.title,
                status=item.status.value,
                suggested_status=item.suggested_status.value,
                blocking=item.blocking,
                outstanding=item.outstanding,
                notes=item.notes,
                provenance_json=provenance_to_dict(item.provenance),
            )
            for item in plan.checklist
        ]
        await self.repository.add_items(item_rows)
        validation = CaseReviewValidationRecord(
            run_id=run.id,
            case_id=case_id,
            validation_pct=plan.metrics.validation_pct,
            evidence_coverage_pct=plan.metrics.evidence_coverage_pct,
            review_completion_pct=plan.metrics.review_completion_pct,
            approval_completion_pct=plan.metrics.approval_completion_pct,
            outstanding_issues=plan.metrics.outstanding_issues,
            blocking_issues=plan.metrics.blocking_issues,
            metrics_json=self._metrics(plan.metrics).model_dump(),
            provenance_json={
                **plan.provenance,
                "engine_version": CR_ENGINE_VERSION,
                "policy_version": CR_POLICY_VERSION,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
        await self.repository.add_validation(validation)
        await self.session.commit()
        await self.session.refresh(run)
        return await self._hydrate(run)

    async def preview(self, case_id: UUID) -> CaseReviewPreviewResponse:
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        plan = await self.engine.plan(case)
        return CaseReviewPreviewResponse(
            case_id=case_id,
            status=RunStatus.SUCCEEDED.value,
            stage=plan.stage.value,
            checklist_count=len(plan.checklist),
            approval_count=0,
            metrics=self._metrics(plan.metrics),
            outstanding=plan.outstanding,
            blocking=plan.blocking,
            required_roles=plan.required_approver_roles,
            provenance=plan.provenance,
            engine_version=CR_ENGINE_VERSION,
            policy_version=CR_POLICY_VERSION,
            checklist=self._plan_to_drafts(case_id, plan),
            approvals=[],
            persisted=False,
        )

    async def get_latest(self, case_id: UUID) -> CaseReviewRunResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            raise CaseReviewNotFoundError("No case review for this case.")
        return await self._hydrate(run)

    async def get_run(self, run_id: UUID) -> CaseReviewRunResponse:
        run = await self.repository.get_run(run_id)
        if run is None:
            raise CaseReviewNotFoundError("Case review run not found.")
        return await self._hydrate(run)

    async def list_checklist(
        self,
        case_id: UUID,
    ) -> ChecklistListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            return ChecklistListResponse(items=[], total=0)
        rows = await self.repository.items_for_run(run.id)
        return ChecklistListResponse(
            items=[self._item_response(row) for row in rows],
            total=len(rows),
        )

    async def update_checklist_item(
        self,
        item_id: UUID,
        payload: ChecklistItemUpdateRequest,
    ) -> ChecklistItemResponse:
        item = await self.repository.get_item(item_id)
        if item is None:
            raise ChecklistItemNotFoundError("Checklist item not found.")
        if payload.status is not None:
            status = payload.status.strip().upper()
            allowed = {s.value for s in ChecklistItemStatus}
            if status not in allowed:
                raise CaseReviewError(f"Invalid checklist status: {payload.status}")
            item.status = status
            item.outstanding = status in {
                ChecklistItemStatus.PENDING.value,
                ChecklistItemStatus.FAIL.value,
                ChecklistItemStatus.BLOCKED.value,
            }
            item.blocking = status in {
                ChecklistItemStatus.FAIL.value,
                ChecklistItemStatus.BLOCKED.value,
            }
            item.reviewed_at = datetime.now(UTC)
        if payload.notes is not None:
            item.notes = payload.notes.strip()
        if payload.reviewer is not None:
            item.reviewer = payload.reviewer.strip() or None
            item.reviewed_at = datetime.now(UTC)
        run = await self.repository.get_run(item.run_id)
        if run is not None:
            await self._recompute_stage(run)
        await self.session.commit()
        await self.session.refresh(item)
        return self._item_response(item)

    async def record_approval(
        self,
        payload: ApprovalCreateRequest,
    ) -> ApprovalResponse:
        if await self.repository.get_case(payload.case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        try:
            decision = normalize_approval_decision(payload.decision)
            role = normalize_approver_role(payload.approver_role)
        except ValueError as exc:
            raise CaseReviewError(str(exc)) from exc
        run_id = payload.run_id
        if run_id is None:
            latest = await self.repository.get_latest_run(payload.case_id)
            if latest is None:
                raise CaseReviewNotFoundError("No case review for this case.")
            run_id = latest.id
        run = await self.repository.get_run(run_id)
        if run is None:
            raise CaseReviewNotFoundError("Case review run not found.")
        checklist = await self.repository.get_checklist_for_run(run_id)
        checklist_id = payload.checklist_id or (checklist.id if checklist else None)
        row = CaseReviewApproval(
            run_id=run_id,
            case_id=payload.case_id,
            checklist_id=checklist_id,
            checklist_item_id=payload.checklist_item_id,
            reviewer=payload.reviewer.strip() or "unknown",
            approver_role=role,
            decision=decision,
            comments=payload.comments.strip(),
            provenance_json={
                **dict(payload.provenance or {}),
                "engine_version": CR_ENGINE_VERSION,
                "policy_version": CR_POLICY_VERSION,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
        await self.repository.add_approval(row)
        await self._recompute_stage(run)
        await self.session.commit()
        await self.session.refresh(row)
        return self._approval_response(row)

    async def list_approvals(
        self,
        case_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> ApprovalListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        rows, total = await self.repository.list_approvals_for_case(
            case_id,
            limit=limit,
            offset=offset,
        )
        return ApprovalListResponse(
            items=[self._approval_response(row) for row in rows],
            total=total,
        )

    async def metrics(self, case_id: UUID) -> ValidationMetricsResponse:
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            preview = await self.preview(case_id)
            return preview.metrics
        return self._metrics(run.metrics_json or {})

    async def history(
        self,
        case_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> CaseReviewHistoryResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        rows, total = await self.repository.list_runs(
            case_id,
            limit=limit,
            offset=offset,
        )
        return CaseReviewHistoryResponse(
            items=[
                CaseReviewHistoryItem(
                    id=row.id,
                    case_id=row.case_id,
                    status=row.status,
                    stage=row.stage,
                    checklist_count=row.checklist_count,
                    approval_count=row.approval_count,
                    metrics=self._metrics(row.metrics_json or {}),
                    engine_version=row.engine_version,
                    policy_version=row.policy_version,
                    created_at=row.created_at,
                    completed_at=row.completed_at,
                )
                for row in rows
            ],
            total=total,
        )
