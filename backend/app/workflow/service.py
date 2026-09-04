"""Application service for investigation workflow lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.models import AuthenticatedPrincipal
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.models.audio_ai import AudioAnalysisRun
from backend.app.models.correlation import CorrelationAnalysisRun
from backend.app.models.document_ai import DocumentAnalysisRun
from backend.app.models.evidence import Evidence
from backend.app.models.fusion import FusionAnalysisRun
from backend.app.models.image_ai import ImageAnalysisRun
from backend.app.models.signature_ai import SignatureVerificationRun
from backend.app.models.timeline import InvestigationTimeline
from backend.app.models.video_ai import VideoAnalysisRun
from backend.app.models.workflow import (
    InvestigationWorkflow,
    WorkflowMilestone,
    WorkflowNote,
    WorkflowReview,
    WorkflowTask,
)
from backend.app.workflow.audit import record_workflow_audit
from backend.app.workflow.engine import (
    allowed_status_transitions,
    assert_report_approval_transition,
    assert_status_transition,
    assert_task_transition,
    can_publish_report,
)
from backend.app.workflow.exceptions import (
    InvalidReviewTransitionError,
    ReportNotApprovedError,
    WorkflowError,
)
from backend.app.workflow.notifications import create_workflow_notification
from backend.app.workflow.policy import (
    ENGINE_VERSION,
    WORKFLOW_POLICY_VERSION,
    ActivityAction,
    EvidenceReviewStatus,
    InvestigationStatus,
    MilestoneType,
    NoteCategory,
    NoteVisibility,
    NotificationKind,
    ReportApprovalStatus,
    ReviewKind,
    TaskStatus,
    TaskType,
)
from backend.app.workflow.repository import WorkflowRepository
from backend.app.workflow.schemas import (
    MilestoneListResponse,
    MilestoneResponse,
    NoteListResponse,
    NoteResponse,
    NotificationListResponse,
    NotificationResponse,
    ReviewListResponse,
    ReviewResponse,
    TaskListResponse,
    TaskResponse,
    WorkflowResponse,
)
from backend.app.workflow.timeline import append_activity


def _actor(
    principal: AuthenticatedPrincipal | None,
) -> tuple[UUID | None, str]:
    if principal is None:
        return None, "system"
    return principal.user_id, principal.username


class WorkflowService:
    """Manage investigation status, tasks, reviews, notes, milestones."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = WorkflowRepository(session)

    async def _require_case(self, case_id: UUID) -> None:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("The case was not found.")

    async def _workflow_response(
        self, row: InvestigationWorkflow,
    ) -> WorkflowResponse:
        return WorkflowResponse(
            id=row.id,
            case_id=row.case_id,
            status=row.status,
            assigned_analyst_id=row.assigned_analyst_id,
            allowed_transitions=allowed_status_transitions(row.status),
            activity=list(row.activity_json or []),
            policy_version=row.policy_version,
            engine_version=row.engine_version,
            created_at=row.created_at,
            updated_at=row.updated_at,
            status_changed_at=row.status_changed_at,
            status_changed_by=row.status_changed_by,
        )

    def _task_response(self, row: WorkflowTask) -> TaskResponse:
        return TaskResponse(
            id=row.id,
            workflow_id=row.workflow_id,
            case_id=row.case_id,
            task_type=row.task_type,
            title=row.title,
            description=row.description,
            status=row.status,
            assignee_id=row.assignee_id,
            created_by=row.created_by,
            linked_evidence_id=row.linked_evidence_id,
            linked_report_id=row.linked_report_id,
            completed_at=row.completed_at,
            cancelled_at=row.cancelled_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _note_response(self, row: WorkflowNote) -> NoteResponse:
        return NoteResponse(
            id=row.id,
            workflow_id=row.workflow_id,
            case_id=row.case_id,
            category=row.category,
            visibility=row.visibility,
            content_markdown=row.content_markdown,
            author_id=row.author_id,
            history=list(row.history_json or []),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _review_response(self, row: WorkflowReview) -> ReviewResponse:
        return ReviewResponse(
            id=row.id,
            workflow_id=row.workflow_id,
            case_id=row.case_id,
            review_kind=row.review_kind,
            status=row.status,
            evidence_id=row.evidence_id,
            report_id=row.report_id,
            reviewer_id=row.reviewer_id,
            comments=row.comments,
            reason=row.reason,
            decided_at=row.decided_at,
            history=list(row.history_json or []),
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _milestone_response(
        self, row: WorkflowMilestone,
    ) -> MilestoneResponse:
        return MilestoneResponse(
            id=row.id,
            workflow_id=row.workflow_id,
            case_id=row.case_id,
            milestone_type=row.milestone_type,
            label=row.label,
            reached_at=row.reached_at,
            reached_by=row.reached_by,
            auto_derived=row.auto_derived,
            details=dict(row.details_json or {}),
            created_at=row.created_at,
        )

    def _notification_response(
        self, row: Any,
    ) -> NotificationResponse:
        return NotificationResponse(
            id=row.id,
            workflow_id=row.workflow_id,
            case_id=row.case_id,
            user_id=row.user_id,
            kind=row.kind,
            title=row.title,
            body=row.body,
            status=row.status,
            payload=dict(row.payload_json or {}),
            created_at=row.created_at,
        )

    async def _reach_milestone(
        self,
        workflow: InvestigationWorkflow,
        milestone: MilestoneType,
        *,
        actor_id: UUID | None,
        actor_username: str,
        auto_derived: bool = False,
        details: dict[str, Any] | None = None,
    ) -> WorkflowMilestone | None:
        existing = await self.repository.get_milestone(
            workflow.id, milestone.value,
        )
        if existing is not None:
            return None
        row = WorkflowMilestone(
            workflow_id=workflow.id,
            case_id=workflow.case_id,
            milestone_type=milestone.value,
            label=milestone.value,
            reached_by=actor_id,
            auto_derived=auto_derived,
            details_json=details or {},
        )
        await self.repository.add(row)
        await self.session.flush()
        await append_activity(
            self.session,
            workflow,
            action=ActivityAction.MILESTONE_REACHED.value,
            summary=f"Milestone reached: {milestone.value}",
            actor_id=actor_id,
            actor_username=actor_username,
            details={"milestone": milestone.value, "auto_derived": auto_derived},
        )
        await record_workflow_audit(
            self.session,
            operation="workflow.milestone_reached",
            case_id=workflow.case_id,
            user=actor_username,
            new_state={"milestone": milestone.value},
        )
        return row

    async def _derive_milestones(
        self,
        workflow: InvestigationWorkflow,
        *,
        actor_id: UUID | None,
        actor_username: str,
    ) -> None:
        case_id = workflow.case_id
        if await self.repository.count_evidence(case_id) > 0:
            await self._reach_milestone(
                workflow,
                MilestoneType.EVIDENCE_COLLECTION_COMPLETE,
                actor_id=actor_id,
                actor_username=actor_username,
                auto_derived=True,
            )

        ai_found = False
        for model in (
            ImageAnalysisRun,
            DocumentAnalysisRun,
            VideoAnalysisRun,
            AudioAnalysisRun,
        ):
            result = await self.session.execute(
                select(model.id)
                .join(Evidence, model.evidence_id == Evidence.id)
                .where(Evidence.case_id == case_id)
                .limit(1)
            )
            if result.scalar_one_or_none() is not None:
                ai_found = True
                break
        if not ai_found:
            sig = await self.session.execute(
                select(SignatureVerificationRun.id)
                .join(
                    Evidence,
                    SignatureVerificationRun.questioned_evidence_id
                    == Evidence.id,
                )
                .where(Evidence.case_id == case_id)
                .limit(1)
            )
            ai_found = sig.scalar_one_or_none() is not None
        if ai_found:
            await self._reach_milestone(
                workflow,
                MilestoneType.AI_ANALYSIS_COMPLETE,
                actor_id=actor_id,
                actor_username=actor_username,
                auto_derived=True,
            )

        fusion = await self.session.execute(
            select(FusionAnalysisRun.id)
            .join(Evidence, FusionAnalysisRun.evidence_id == Evidence.id)
            .where(Evidence.case_id == case_id)
            .limit(1)
        )
        if fusion.scalar_one_or_none() is not None:
            await self._reach_milestone(
                workflow,
                MilestoneType.FUSION_COMPLETE,
                actor_id=actor_id,
                actor_username=actor_username,
                auto_derived=True,
            )

        corr = await self.session.execute(
            select(CorrelationAnalysisRun.id)
            .where(CorrelationAnalysisRun.case_id == case_id)
            .limit(1)
        )
        if corr.scalar_one_or_none() is not None:
            await self._reach_milestone(
                workflow,
                MilestoneType.CORRELATION_COMPLETE,
                actor_id=actor_id,
                actor_username=actor_username,
                auto_derived=True,
            )

        timeline = await self.session.execute(
            select(InvestigationTimeline.id)
            .where(InvestigationTimeline.case_id == case_id)
            .limit(1)
        )
        if timeline.scalar_one_or_none() is not None:
            await self._reach_milestone(
                workflow,
                MilestoneType.TIMELINE_COMPLETE,
                actor_id=actor_id,
                actor_username=actor_username,
                auto_derived=True,
            )

        if await self.repository.count_reports(case_id) > 0:
            await self._reach_milestone(
                workflow,
                MilestoneType.REPORT_DRAFTED,
                actor_id=actor_id,
                actor_username=actor_username,
                auto_derived=True,
            )

        if workflow.status == InvestigationStatus.APPROVED.value:
            await self._reach_milestone(
                workflow,
                MilestoneType.REPORT_APPROVED,
                actor_id=actor_id,
                actor_username=actor_username,
                auto_derived=True,
            )
        if workflow.status in {
            InvestigationStatus.REPORTED.value,
            InvestigationStatus.ARCHIVED.value,
        }:
            await self._reach_milestone(
                workflow,
                MilestoneType.CASE_CLOSED,
                actor_id=actor_id,
                actor_username=actor_username,
                auto_derived=True,
            )

    async def ensure_workflow(
        self,
        case_id: UUID,
        principal: AuthenticatedPrincipal | None = None,
    ) -> InvestigationWorkflow:
        await self._require_case(case_id)
        existing = await self.repository.get_workflow_by_case(case_id)
        if existing is not None:
            return existing
        actor_id, actor_username = _actor(principal)
        row = InvestigationWorkflow(
            case_id=case_id,
            status=InvestigationStatus.NEW.value,
            policy_version=WORKFLOW_POLICY_VERSION,
            engine_version=ENGINE_VERSION,
            created_by=actor_id,
            activity_json=[],
        )
        await self.repository.add(row)
        await self.session.flush()
        await append_activity(
            self.session,
            row,
            action=ActivityAction.WORKFLOW_INITIALIZED.value,
            summary="Investigation workflow initialized",
            actor_id=actor_id,
            actor_username=actor_username,
        )
        await self._reach_milestone(
            row,
            MilestoneType.INVESTIGATION_STARTED,
            actor_id=actor_id,
            actor_username=actor_username,
            auto_derived=True,
        )
        await record_workflow_audit(
            self.session,
            operation="workflow.initialized",
            case_id=case_id,
            user=actor_username,
            new_state={"status": row.status},
        )
        await self.session.commit()
        loaded = await self.repository.get_workflow_by_case(case_id)
        assert loaded is not None
        return loaded

    async def get_workflow(
        self,
        case_id: UUID,
        principal: AuthenticatedPrincipal | None = None,
    ) -> WorkflowResponse:
        workflow = await self.ensure_workflow(case_id, principal)
        actor_id, actor_username = _actor(principal)
        await self._derive_milestones(
            workflow,
            actor_id=actor_id,
            actor_username=actor_username,
        )
        await self.session.commit()
        refreshed = await self.repository.get_workflow_by_case(case_id)
        assert refreshed is not None
        return await self._workflow_response(refreshed)

    async def update_status(
        self,
        case_id: UUID,
        *,
        status: str,
        assigned_analyst_id: UUID | None,
        principal: AuthenticatedPrincipal | None,
    ) -> WorkflowResponse:
        workflow = await self.ensure_workflow(case_id, principal)
        actor_id, actor_username = _actor(principal)
        previous = workflow.status
        target = assert_status_transition(previous, status)
        if assigned_analyst_id is not None:
            user = await self.repository.get_user(assigned_analyst_id)
            if user is None:
                raise ResourceNotFoundError("The analyst was not found.")
            workflow.assigned_analyst_id = assigned_analyst_id
        workflow.status = target.value
        workflow.status_changed_at = datetime.now(UTC)
        workflow.status_changed_by = actor_id
        await append_activity(
            self.session,
            workflow,
            action=ActivityAction.STATUS_CHANGED.value,
            summary=f"Status changed from {previous} to {target.value}",
            actor_id=actor_id,
            actor_username=actor_username,
            details={"from": previous, "to": target.value},
        )
        await record_workflow_audit(
            self.session,
            operation="workflow.status_changed",
            case_id=case_id,
            user=actor_username,
            previous_state={"status": previous},
            new_state={"status": target.value},
        )
        if target is InvestigationStatus.ARCHIVED:
            if workflow.assigned_analyst_id is not None:
                await create_workflow_notification(
                    self.session,
                    workflow_id=workflow.id,
                    case_id=case_id,
                    user_id=workflow.assigned_analyst_id,
                    kind=NotificationKind.WORKFLOW_COMPLETED.value,
                    title="Investigation workflow completed",
                    body="Investigation reached ARCHIVED status.",
                    payload={"status": target.value},
                )
        await self._derive_milestones(
            workflow,
            actor_id=actor_id,
            actor_username=actor_username,
        )
        await self.session.commit()
        refreshed = await self.repository.get_workflow_by_case(case_id)
        assert refreshed is not None
        return await self._workflow_response(refreshed)

    async def list_tasks(self, case_id: UUID) -> TaskListResponse:
        await self.ensure_workflow(case_id)
        rows = await self.repository.list_tasks(case_id)
        items = [self._task_response(row) for row in rows]
        return TaskListResponse(items=items, total=len(items))

    async def create_task(
        self,
        case_id: UUID,
        *,
        title: str,
        task_type: str,
        description: str | None,
        assignee_id: UUID | None,
        linked_evidence_id: UUID | None,
        linked_report_id: UUID | None,
        principal: AuthenticatedPrincipal | None,
    ) -> TaskResponse:
        workflow = await self.ensure_workflow(case_id, principal)
        actor_id, actor_username = _actor(principal)
        try:
            typed = TaskType(task_type)
        except ValueError as exc:
            raise WorkflowError(f"Unknown task type: {task_type}") from exc
        if linked_evidence_id is not None:
            evidence = await self.repository.get_evidence(linked_evidence_id)
            if evidence is None or evidence.case_id != case_id:
                raise ResourceNotFoundError("The evidence was not found.")
        if linked_report_id is not None:
            report = await self.repository.get_report(linked_report_id)
            if report is None or report.case_id != case_id:
                raise ResourceNotFoundError("The report was not found.")
        status = TaskStatus.OPEN.value
        if assignee_id is not None:
            user = await self.repository.get_user(assignee_id)
            if user is None:
                raise ResourceNotFoundError("The assignee was not found.")
            status = TaskStatus.ASSIGNED.value
        row = WorkflowTask(
            workflow_id=workflow.id,
            case_id=case_id,
            task_type=typed.value,
            title=title,
            description=description,
            status=status,
            assignee_id=assignee_id,
            created_by=actor_id,
            linked_evidence_id=linked_evidence_id,
            linked_report_id=linked_report_id,
        )
        await self.repository.add(row)
        await self.session.flush()
        await append_activity(
            self.session,
            workflow,
            action=ActivityAction.TASK_CREATED.value,
            summary=f"Task created: {title}",
            actor_id=actor_id,
            actor_username=actor_username,
            details={"task_id": str(row.id), "task_type": typed.value},
        )
        await record_workflow_audit(
            self.session,
            operation="workflow.task_created",
            case_id=case_id,
            user=actor_username,
            new_state={"task_id": str(row.id), "title": title},
        )
        if assignee_id is not None:
            await append_activity(
                self.session,
                workflow,
                action=ActivityAction.TASK_ASSIGNED.value,
                summary=f"Task assigned: {title}",
                actor_id=actor_id,
                actor_username=actor_username,
                details={
                    "task_id": str(row.id),
                    "assignee_id": str(assignee_id),
                },
            )
            await create_workflow_notification(
                self.session,
                workflow_id=workflow.id,
                case_id=case_id,
                user_id=assignee_id,
                kind=NotificationKind.ASSIGNED_TASK.value,
                title="Task assigned",
                body=f"You were assigned: {title}",
                payload={"task_id": str(row.id)},
            )
        await self.session.commit()
        loaded = await self.repository.get_task(row.id)
        assert loaded is not None
        return self._task_response(loaded)

    async def update_task(
        self,
        task_id: UUID,
        *,
        title: str | None,
        description: str | None,
        assignee_id: UUID | None,
        status: str | None,
        action: str | None,
        principal: AuthenticatedPrincipal | None,
    ) -> TaskResponse:
        row = await self.repository.get_task(task_id)
        if row is None:
            raise ResourceNotFoundError("The task was not found.")
        workflow = await self.repository.get_workflow(row.workflow_id)
        if workflow is None:
            raise ResourceNotFoundError("The workflow was not found.")
        actor_id, actor_username = _actor(principal)
        if title is not None:
            row.title = title
        if description is not None:
            row.description = description

        target_status = status
        if action is not None:
            normalized = action.strip().lower()
            if normalized == "assign":
                if assignee_id is None and row.assignee_id is None:
                    raise WorkflowError(
                        "assignee_id is required to assign a task."
                    )
                target_status = TaskStatus.ASSIGNED.value
            elif normalized == "complete":
                target_status = TaskStatus.COMPLETED.value
            elif normalized == "reopen":
                target_status = TaskStatus.REOPENED.value
            elif normalized == "cancel":
                target_status = TaskStatus.CANCELLED.value
            else:
                raise WorkflowError(f"Unknown task action: {action}")

        if assignee_id is not None:
            user = await self.repository.get_user(assignee_id)
            if user is None:
                raise ResourceNotFoundError("The assignee was not found.")
            previous_assignee = row.assignee_id
            row.assignee_id = assignee_id
            if previous_assignee != assignee_id:
                await append_activity(
                    self.session,
                    workflow,
                    action=ActivityAction.TASK_ASSIGNED.value,
                    summary=f"Task assigned: {row.title}",
                    actor_id=actor_id,
                    actor_username=actor_username,
                    details={
                        "task_id": str(row.id),
                        "assignee_id": str(assignee_id),
                    },
                )
                await create_workflow_notification(
                    self.session,
                    workflow_id=workflow.id,
                    case_id=row.case_id,
                    user_id=assignee_id,
                    kind=NotificationKind.ASSIGNED_TASK.value,
                    title="Task assigned",
                    body=f"You were assigned: {row.title}",
                    payload={"task_id": str(row.id)},
                )
                if target_status is None and row.status in {
                    TaskStatus.OPEN.value,
                    TaskStatus.REOPENED.value,
                }:
                    target_status = TaskStatus.ASSIGNED.value

        if target_status is not None:
            previous = row.status
            next_status = assert_task_transition(previous, target_status)
            row.status = next_status.value
            if next_status is TaskStatus.COMPLETED:
                row.completed_at = datetime.now(UTC)
                await append_activity(
                    self.session,
                    workflow,
                    action=ActivityAction.TASK_COMPLETED.value,
                    summary=f"Task completed: {row.title}",
                    actor_id=actor_id,
                    actor_username=actor_username,
                    details={"task_id": str(row.id)},
                )
            elif next_status is TaskStatus.REOPENED:
                row.completed_at = None
                row.cancelled_at = None
                await append_activity(
                    self.session,
                    workflow,
                    action=ActivityAction.TASK_REOPENED.value,
                    summary=f"Task reopened: {row.title}",
                    actor_id=actor_id,
                    actor_username=actor_username,
                    details={"task_id": str(row.id)},
                )
            elif next_status is TaskStatus.CANCELLED:
                row.cancelled_at = datetime.now(UTC)
                await append_activity(
                    self.session,
                    workflow,
                    action=ActivityAction.TASK_CANCELLED.value,
                    summary=f"Task cancelled: {row.title}",
                    actor_id=actor_id,
                    actor_username=actor_username,
                    details={"task_id": str(row.id)},
                )
            await record_workflow_audit(
                self.session,
                operation="workflow.task_updated",
                case_id=row.case_id,
                user=actor_username,
                previous_state={"status": previous},
                new_state={"status": next_status.value, "task_id": str(row.id)},
            )

        await self.session.commit()
        loaded = await self.repository.get_task(task_id)
        assert loaded is not None
        return self._task_response(loaded)

    async def list_notes(self, case_id: UUID) -> NoteListResponse:
        await self.ensure_workflow(case_id)
        rows = await self.repository.list_notes(case_id)
        items = [self._note_response(row) for row in rows]
        return NoteListResponse(items=items, total=len(items))

    async def create_note(
        self,
        case_id: UUID,
        *,
        content_markdown: str,
        category: str,
        visibility: str,
        principal: AuthenticatedPrincipal | None,
    ) -> NoteResponse:
        workflow = await self.ensure_workflow(case_id, principal)
        actor_id, actor_username = _actor(principal)
        try:
            cat = NoteCategory(category)
            vis = NoteVisibility(visibility)
        except ValueError as exc:
            raise WorkflowError("Invalid note category or visibility.") from exc
        now = datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        )
        history = [
            {
                "version": 1,
                "content_markdown": content_markdown,
                "author_id": str(actor_id) if actor_id else None,
                "author_username": actor_username,
                "timestamp": now,
            }
        ]
        row = WorkflowNote(
            workflow_id=workflow.id,
            case_id=case_id,
            category=cat.value,
            visibility=vis.value,
            content_markdown=content_markdown,
            author_id=actor_id,
            history_json=history,
        )
        await self.repository.add(row)
        await self.session.flush()
        await append_activity(
            self.session,
            workflow,
            action=ActivityAction.NOTE_CREATED.value,
            summary="Investigation note created",
            actor_id=actor_id,
            actor_username=actor_username,
            details={"note_id": str(row.id), "category": cat.value},
        )
        await record_workflow_audit(
            self.session,
            operation="workflow.note_created",
            case_id=case_id,
            user=actor_username,
            new_state={"note_id": str(row.id)},
        )
        await self.session.commit()
        return self._note_response(row)

    async def list_reviews(self, case_id: UUID) -> ReviewListResponse:
        await self.ensure_workflow(case_id)
        rows = await self.repository.list_reviews(case_id)
        items = [self._review_response(row) for row in rows]
        return ReviewListResponse(items=items, total=len(items))

    async def create_review(
        self,
        case_id: UUID,
        *,
        review_kind: str,
        status: str | None,
        evidence_id: UUID | None,
        report_id: UUID | None,
        reviewer_id: UUID | None,
        comments: str | None,
        reason: str | None,
        principal: AuthenticatedPrincipal | None,
    ) -> ReviewResponse:
        workflow = await self.ensure_workflow(case_id, principal)
        actor_id, actor_username = _actor(principal)
        try:
            kind = ReviewKind(review_kind)
        except ValueError as exc:
            raise WorkflowError(f"Unknown review kind: {review_kind}") from exc

        if kind is ReviewKind.EVIDENCE:
            if evidence_id is None:
                raise WorkflowError("evidence_id is required for evidence review.")
            evidence = await self.repository.get_evidence(evidence_id)
            if evidence is None or evidence.case_id != case_id:
                raise ResourceNotFoundError("The evidence was not found.")
            initial = status or EvidenceReviewStatus.PENDING.value
            try:
                EvidenceReviewStatus(initial)
            except ValueError as exc:
                raise InvalidReviewTransitionError(
                    f"Unknown evidence review status: {initial}"
                ) from exc
        else:
            if report_id is None:
                raise WorkflowError("report_id is required for report review.")
            report = await self.repository.get_report(report_id)
            if report is None or report.case_id != case_id:
                raise ResourceNotFoundError("The report was not found.")
            initial = status or ReportApprovalStatus.DRAFT.value
            try:
                ReportApprovalStatus(initial)
            except ValueError as exc:
                raise InvalidReviewTransitionError(
                    f"Unknown report approval status: {initial}"
                ) from exc
            if initial == ReportApprovalStatus.PUBLISHED.value:
                raise ReportNotApprovedError(
                    "Reports cannot publish unless approved."
                )

        assigned_reviewer = reviewer_id or actor_id
        if assigned_reviewer is not None:
            user = await self.repository.get_user(assigned_reviewer)
            if user is None:
                raise ResourceNotFoundError("The reviewer was not found.")

        now = datetime.now(UTC)
        decided_at = None
        if (
            kind is ReviewKind.EVIDENCE
            and initial != EvidenceReviewStatus.PENDING.value
        ):
            decided_at = now
        if kind is ReviewKind.REPORT and initial not in {
            ReportApprovalStatus.DRAFT.value,
            ReportApprovalStatus.REVIEW.value,
        }:
            decided_at = now

        history_entry = {
            "status": initial,
            "reviewer_id": str(assigned_reviewer) if assigned_reviewer else None,
            "comments": comments,
            "reason": reason,
            "timestamp": now.replace(microsecond=0).isoformat().replace(
                "+00:00", "Z"
            ),
        }
        row = WorkflowReview(
            workflow_id=workflow.id,
            case_id=case_id,
            review_kind=kind.value,
            status=initial,
            evidence_id=evidence_id,
            report_id=report_id,
            reviewer_id=assigned_reviewer,
            comments=comments,
            reason=reason,
            decided_at=decided_at,
            history_json=[history_entry],
            created_by=actor_id,
        )
        await self.repository.add(row)
        await self.session.flush()

        await append_activity(
            self.session,
            workflow,
            action=ActivityAction.REVIEW_REQUESTED.value,
            summary=f"{kind.value} review requested",
            actor_id=actor_id,
            actor_username=actor_username,
            details={
                "review_id": str(row.id),
                "status": initial,
                "review_kind": kind.value,
            },
        )
        if assigned_reviewer is not None:
            await create_workflow_notification(
                self.session,
                workflow_id=workflow.id,
                case_id=case_id,
                user_id=assigned_reviewer,
                kind=NotificationKind.REVIEW_REQUEST.value,
                title="Review requested",
                body=f"A {kind.value} review requires your attention.",
                payload={"review_id": str(row.id)},
            )
            if initial in {
                EvidenceReviewStatus.NEEDS_REVIEW.value,
                ReportApprovalStatus.REVIEW.value,
            }:
                await create_workflow_notification(
                    self.session,
                    workflow_id=workflow.id,
                    case_id=case_id,
                    user_id=assigned_reviewer,
                    kind=NotificationKind.APPROVAL_REQUIRED.value,
                    title="Approval required",
                    body=f"Approval required for {kind.value} review.",
                    payload={"review_id": str(row.id)},
                )

        if (
            kind is ReviewKind.EVIDENCE
            and initial == EvidenceReviewStatus.APPROVED.value
        ):
            await append_activity(
                self.session,
                workflow,
                action=ActivityAction.EVIDENCE_APPROVED.value,
                summary="Evidence approved",
                actor_id=actor_id,
                actor_username=actor_username,
                details={
                    "review_id": str(row.id),
                    "evidence_id": str(evidence_id),
                },
            )
        if kind is ReviewKind.REPORT:
            if initial == ReportApprovalStatus.APPROVED.value:
                await append_activity(
                    self.session,
                    workflow,
                    action=ActivityAction.REPORT_APPROVED.value,
                    summary="Report approved",
                    actor_id=actor_id,
                    actor_username=actor_username,
                    details={"review_id": str(row.id), "report_id": str(report_id)},
                )
                await self._reach_milestone(
                    workflow,
                    MilestoneType.REPORT_APPROVED,
                    actor_id=actor_id,
                    actor_username=actor_username,
                )
            if initial == ReportApprovalStatus.PUBLISHED.value:
                raise ReportNotApprovedError(
                    "Reports cannot publish unless approved."
                )

        await record_workflow_audit(
            self.session,
            operation="workflow.review_created",
            case_id=case_id,
            user=actor_username,
            evidence_id=evidence_id,
            new_state={
                "review_id": str(row.id),
                "review_kind": kind.value,
                "status": initial,
            },
        )
        await self.session.commit()
        return self._review_response(row)

    async def transition_review(
        self,
        review_id: UUID,
        *,
        status: str,
        comments: str | None,
        reason: str | None,
        principal: AuthenticatedPrincipal | None,
    ) -> ReviewResponse:
        """Advance an existing review (used by PATCH if exposed)."""

        row = await self.session.get(WorkflowReview, review_id)
        if row is None:
            raise ResourceNotFoundError("The review was not found.")
        workflow = await self.repository.get_workflow(row.workflow_id)
        if workflow is None:
            raise ResourceNotFoundError("The workflow was not found.")
        actor_id, actor_username = _actor(principal)
        previous = row.status

        if row.review_kind == ReviewKind.EVIDENCE.value:
            try:
                EvidenceReviewStatus(status)
            except ValueError as exc:
                raise InvalidReviewTransitionError(
                    f"Unknown evidence review status: {status}"
                ) from exc
            next_status = status
        else:
            next_enum = assert_report_approval_transition(previous, status)
            if (
                next_enum is ReportApprovalStatus.PUBLISHED
                and not can_publish_report(previous)
            ):
                raise ReportNotApprovedError(
                    "Reports cannot publish unless approved."
                )
            next_status = next_enum.value

        now = datetime.now(UTC)
        history = list(row.history_json or [])
        history.append(
            {
                "status": next_status,
                "reviewer_id": str(actor_id) if actor_id else None,
                "comments": comments,
                "reason": reason,
                "timestamp": now.replace(microsecond=0).isoformat().replace(
                    "+00:00", "Z"
                ),
                "previous_status": previous,
            }
        )
        row.status = next_status
        row.history_json = history
        if comments is not None:
            row.comments = comments
        if reason is not None:
            row.reason = reason
        row.reviewer_id = actor_id or row.reviewer_id
        row.decided_at = now

        await append_activity(
            self.session,
            workflow,
            action=ActivityAction.REVIEW_COMPLETED.value,
            summary=f"Review updated to {next_status}",
            actor_id=actor_id,
            actor_username=actor_username,
            details={
                "review_id": str(row.id),
                "from": previous,
                "to": next_status,
            },
        )
        if (
            row.review_kind == ReviewKind.REPORT.value
            and next_status == ReportApprovalStatus.PUBLISHED.value
        ):
            if actor_id is not None:
                await create_workflow_notification(
                    self.session,
                    workflow_id=workflow.id,
                    case_id=row.case_id,
                    user_id=actor_id,
                    kind=NotificationKind.REPORT_PUBLISHED.value,
                    title="Report published",
                    body="A forensic report was published.",
                    payload={"review_id": str(row.id)},
                )
            await append_activity(
                self.session,
                workflow,
                action=ActivityAction.REPORT_PUBLISHED.value,
                summary="Report published",
                actor_id=actor_id,
                actor_username=actor_username,
                details={"review_id": str(row.id)},
            )
        await record_workflow_audit(
            self.session,
            operation="workflow.review_updated",
            case_id=row.case_id,
            user=actor_username,
            previous_state={"status": previous},
            new_state={"status": next_status, "review_id": str(row.id)},
        )
        await self.session.commit()
        return self._review_response(row)

    async def list_milestones(
        self, case_id: UUID, principal: AuthenticatedPrincipal | None = None,
    ) -> MilestoneListResponse:
        workflow = await self.ensure_workflow(case_id, principal)
        actor_id, actor_username = _actor(principal)
        await self._derive_milestones(
            workflow,
            actor_id=actor_id,
            actor_username=actor_username,
        )
        await self.session.commit()
        rows = await self.repository.list_milestones(case_id)
        items = [self._milestone_response(row) for row in rows]
        return MilestoneListResponse(items=items, total=len(items))

    async def list_notifications(
        self, case_id: UUID,
    ) -> NotificationListResponse:
        await self.ensure_workflow(case_id)
        rows = await self.repository.list_notifications(case_id)
        items = [self._notification_response(row) for row in rows]
        return NotificationListResponse(items=items, total=len(items))
