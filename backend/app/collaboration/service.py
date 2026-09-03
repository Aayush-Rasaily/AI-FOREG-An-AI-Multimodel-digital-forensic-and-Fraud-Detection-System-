"""Application service for case collaboration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.models import AuthenticatedPrincipal
from backend.app.collaboration.activity import record_activity
from backend.app.collaboration.approvals import apply_review_decision
from backend.app.collaboration.comments import (
    append_edit_history,
    extract_mention_usernames,
    soft_delete_comment,
)
from backend.app.collaboration.exceptions import (
    CollaborationConflictError,
    CollaborationError,
    CollaborationForbiddenError,
)
from backend.app.collaboration.notifications import create_notification
from backend.app.collaboration.policy import (
    MEMBER_MANAGE_ROLES,
    CaseMemberRole,
    CaseWorkflowStage,
    NotificationKind,
    ReviewState,
    TaskStatus,
)
from backend.app.collaboration.repository import CollaborationRepository
from backend.app.collaboration.schemas import (
    ActivityListResponse,
    ActivityResponse,
    CaseMemberListResponse,
    CaseMemberResponse,
    CommentListResponse,
    CommentResponse,
    EvidenceAssignmentListResponse,
    EvidenceAssignmentResponse,
    NotificationListResponse,
    NotificationResponse,
    ReviewResponse,
    TaskListResponse,
    TaskResponse,
    WorkflowResponse,
)
from backend.app.collaboration.workflow import allowed_transitions, assert_transition
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.models.collaboration import (
    CaseMember,
    CaseWorkflowState,
    EvidenceAssignment,
    InvestigationComment,
    InvestigationMention,
    InvestigationReview,
    InvestigationTask,
)
from backend.app.models.user import User


class CollaborationService:
    """Manage membership, tasks, comments, reviews, and workflow."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CollaborationRepository(session)

    async def _require_case(self, case_id: UUID) -> None:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("The case was not found.")

    async def _require_user(self, user_id: UUID) -> User:
        user = await self.repository.get_user(user_id)
        if user is None:
            raise ResourceNotFoundError("The user was not found.")
        return user

    async def _member_response(self, row: CaseMember) -> CaseMemberResponse:
        user = await self.repository.get_user(row.user_id)
        return CaseMemberResponse(
            id=row.id,
            case_id=row.case_id,
            user_id=row.user_id,
            username=user.username if user else None,
            display_name=user.display_name if user else None,
            role=row.role,
            invited_by=row.invited_by,
            created_at=row.created_at,
        )

    async def _assert_can_manage_members(
        self,
        principal: AuthenticatedPrincipal | None,
        case_id: UUID,
    ) -> None:
        if principal is None:
            return
        if principal.has_permission("admin.manage_users"):
            return
        member = await self.repository.get_member_by_user(
            case_id, principal.user_id,
        )
        if member is None or member.role not in {
            item.value for item in MEMBER_MANAGE_ROLES
        }:
            raise CollaborationForbiddenError(
                "Only case owners or lead investigators can manage members."
            )

    async def list_members(self, case_id: UUID) -> CaseMemberListResponse:
        await self._require_case(case_id)
        rows = await self.repository.list_members(case_id)
        items = [await self._member_response(row) for row in rows]
        return CaseMemberListResponse(items=items, total=len(items))

    async def add_member(
        self,
        case_id: UUID,
        *,
        user_id: UUID,
        role: str,
        principal: AuthenticatedPrincipal | None,
    ) -> CaseMemberResponse:
        await self._require_case(case_id)
        await self._assert_can_manage_members(principal, case_id)
        await self._require_user(user_id)
        try:
            CaseMemberRole(role)
        except ValueError as exc:
            raise CollaborationError(f"Unknown member role: {role}") from exc
        existing = await self.repository.get_member_by_user(case_id, user_id)
        if existing is not None:
            raise CollaborationConflictError(
                "That user is already a member of this case."
            )
        row = CaseMember(
            case_id=case_id,
            user_id=user_id,
            role=role,
            invited_by=principal.user_id if principal else None,
        )
        await self.repository.add(row)
        await self.session.flush()
        await create_notification(
            self.session,
            user_id=user_id,
            case_id=case_id,
            kind=NotificationKind.CASE_INVITATION.value,
            title="Case invitation",
            body=f"You were added to a case as {role}.",
            payload={"role": role},
        )
        await record_activity(
            self.session,
            case_id=case_id,
            actor_id=principal.user_id if principal else None,
            actor_username=principal.username if principal else "system",
            action="member.joined",
            summary=f"Member added with role {role}",
            details={"user_id": str(user_id), "role": role},
        )
        await self.session.commit()
        loaded = await self.repository.get_member(case_id, row.id)
        assert loaded is not None
        return await self._member_response(loaded)

    async def update_member(
        self,
        case_id: UUID,
        member_id: UUID,
        *,
        role: str | None,
        transfer_ownership: bool,
        principal: AuthenticatedPrincipal | None,
    ) -> CaseMemberResponse:
        await self._require_case(case_id)
        await self._assert_can_manage_members(principal, case_id)
        row = await self.repository.get_member(case_id, member_id)
        if row is None:
            raise ResourceNotFoundError("The member was not found.")
        if transfer_ownership:
            if principal is None:
                raise CollaborationForbiddenError(
                    "Authentication is required to transfer ownership."
                )
            current_owner = await self.repository.get_member_by_user(
                case_id, principal.user_id,
            )
            if (
                current_owner is None
                or current_owner.role != CaseMemberRole.OWNER.value
            ):
                if not (
                    principal is not None
                    and principal.has_permission("admin.manage_users")
                ):
                    raise CollaborationForbiddenError(
                        "Only the owner can transfer ownership."
                    )
            if current_owner is not None:
                current_owner.role = CaseMemberRole.LEAD_INVESTIGATOR.value
            row.role = CaseMemberRole.OWNER.value
        elif role is not None:
            try:
                CaseMemberRole(role)
            except ValueError as exc:
                raise CollaborationError(f"Unknown member role: {role}") from exc
            if (
                row.role == CaseMemberRole.OWNER.value
                and role != CaseMemberRole.OWNER.value
                and await self.repository.count_owners(case_id) <= 1
            ):
                raise CollaborationError("Cannot demote the last case owner.")
            row.role = role
        await record_activity(
            self.session,
            case_id=case_id,
            actor_id=principal.user_id if principal else None,
            actor_username=principal.username if principal else "system",
            action="member.updated",
            summary="Member role updated",
            details={"member_id": str(member_id), "role": row.role},
        )
        await self.session.commit()
        return await self._member_response(row)

    async def remove_member(
        self,
        case_id: UUID,
        member_id: UUID,
        principal: AuthenticatedPrincipal | None,
    ) -> None:
        await self._require_case(case_id)
        await self._assert_can_manage_members(principal, case_id)
        row = await self.repository.get_member(case_id, member_id)
        if row is None:
            raise ResourceNotFoundError("The member was not found.")
        if (
            row.role == CaseMemberRole.OWNER.value
            and await self.repository.count_owners(case_id) <= 1
        ):
            raise CollaborationError("Cannot remove the last case owner.")
        await self.session.delete(row)
        await record_activity(
            self.session,
            case_id=case_id,
            actor_id=principal.user_id if principal else None,
            actor_username=principal.username if principal else "system",
            action="member.removed",
            summary="Member removed",
            details={"member_id": str(member_id), "user_id": str(row.user_id)},
        )
        await self.session.commit()

    async def assign_evidence(
        self,
        evidence_id: UUID,
        *,
        assignee_id: UUID,
        priority: str,
        due_date: datetime | None,
        notes: str | None,
        principal: AuthenticatedPrincipal | None,
    ) -> EvidenceAssignmentResponse:
        evidence = await self.repository.get_evidence(evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The evidence was not found.")
        await self._require_user(assignee_id)
        row = EvidenceAssignment(
            case_id=evidence.case_id,
            evidence_id=evidence_id,
            assignee_id=assignee_id,
            assigned_by=principal.user_id if principal else assignee_id,
            priority=priority,
            status="pending",
            due_date=due_date,
            notes=notes,
        )
        await self.repository.add(row)
        await self.session.flush()
        await create_notification(
            self.session,
            user_id=assignee_id,
            case_id=evidence.case_id,
            kind=NotificationKind.ASSIGNMENT.value,
            title="Evidence assignment",
            body="Evidence was assigned to you.",
            payload={"evidence_id": str(evidence_id)},
        )
        await record_activity(
            self.session,
            case_id=evidence.case_id,
            actor_id=principal.user_id if principal else None,
            actor_username=principal.username if principal else "system",
            action="assignment.created",
            summary="Evidence assigned",
            details={
                "evidence_id": str(evidence_id),
                "assignee_id": str(assignee_id),
            },
        )
        await self.session.commit()
        return EvidenceAssignmentResponse(
            id=row.id,
            case_id=row.case_id,
            evidence_id=row.evidence_id,
            assignee_id=row.assignee_id,
            assigned_by=row.assigned_by,
            priority=row.priority,
            status=row.status,
            due_date=row.due_date,
            notes=row.notes,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def list_assignments(
        self, evidence_id: UUID,
    ) -> EvidenceAssignmentListResponse:
        if await self.repository.get_evidence(evidence_id) is None:
            raise ResourceNotFoundError("The evidence was not found.")
        rows = await self.repository.list_assignments(evidence_id)
        items = [
            EvidenceAssignmentResponse(
                id=row.id,
                case_id=row.case_id,
                evidence_id=row.evidence_id,
                assignee_id=row.assignee_id,
                assigned_by=row.assigned_by,
                priority=row.priority,
                status=row.status,
                due_date=row.due_date,
                notes=row.notes,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]
        return EvidenceAssignmentListResponse(items=items, total=len(items))

    async def _comment_response(
        self, row: InvestigationComment,
    ) -> CommentResponse:
        user = await self.repository.get_user(row.author_id)
        mentions = await self.repository.list_mentions(row.id)
        return CommentResponse(
            id=row.id,
            case_id=row.case_id,
            author_id=row.author_id,
            author_username=user.username if user else None,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            parent_id=row.parent_id,
            body=row.body,
            body_markdown=row.body_markdown,
            edit_history=list(row.edit_history_json or []),
            is_deleted=row.is_deleted,
            mentions=[item.mentioned_user_id for item in mentions],
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create_comment(
        self,
        *,
        case_id: UUID,
        resource_type: str,
        resource_id: str,
        body: str,
        parent_id: UUID | None,
        body_markdown: bool,
        principal: AuthenticatedPrincipal | None,
    ) -> CommentResponse:
        await self._require_case(case_id)
        if principal is None:
            raise CollaborationForbiddenError("Authentication is required.")
        if parent_id is not None:
            parent = await self.repository.get_comment(parent_id)
            if parent is None or parent.case_id != case_id:
                raise ResourceNotFoundError("The parent comment was not found.")
        row = InvestigationComment(
            case_id=case_id,
            author_id=principal.user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            parent_id=parent_id,
            body=body,
            body_markdown=body_markdown,
            edit_history_json=[],
            is_deleted=False,
        )
        await self.repository.add(row)
        await self.session.flush()
        for username in extract_mention_usernames(body):
            user = await self.repository.get_user_by_username(username)
            if user is None:
                continue
            await self.repository.add(
                InvestigationMention(
                    comment_id=row.id,
                    mentioned_user_id=user.id,
                )
            )
            await create_notification(
                self.session,
                user_id=user.id,
                case_id=case_id,
                kind=NotificationKind.MENTION.value,
                title="You were mentioned",
                body=f"{principal.username} mentioned you in a comment.",
                payload={"comment_id": str(row.id)},
            )
        await record_activity(
            self.session,
            case_id=case_id,
            actor_id=principal.user_id,
            actor_username=principal.username,
            action="comment.created",
            summary="Comment added",
            details={
                "comment_id": str(row.id),
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )
        await self.session.commit()
        loaded = await self.repository.get_comment(row.id)
        assert loaded is not None
        return await self._comment_response(loaded)

    async def list_comments(
        self, resource_type: str, resource_id: str,
    ) -> CommentListResponse:
        rows = await self.repository.list_comments(
            resource_type=resource_type,
            resource_id=resource_id,
        )
        items = [await self._comment_response(row) for row in rows]
        return CommentListResponse(items=items, total=len(items))

    async def update_comment(
        self,
        comment_id: UUID,
        body: str,
        principal: AuthenticatedPrincipal | None,
    ) -> CommentResponse:
        row = await self.repository.get_comment(comment_id)
        if row is None or row.is_deleted:
            raise ResourceNotFoundError("The comment was not found.")
        if principal is None or row.author_id != principal.user_id:
            raise CollaborationForbiddenError("You can only edit your own comments.")
        append_edit_history(row, row.body)
        row.body = body
        await self.session.commit()
        return await self._comment_response(row)

    async def delete_comment(
        self,
        comment_id: UUID,
        principal: AuthenticatedPrincipal | None,
    ) -> CommentResponse:
        row = await self.repository.get_comment(comment_id)
        if row is None:
            raise ResourceNotFoundError("The comment was not found.")
        if principal is None or (
            row.author_id != principal.user_id
            and not principal.has_permission("admin.manage_users")
        ):
            raise CollaborationForbiddenError(
                "You can only delete your own comments."
            )
        soft_delete_comment(row)
        await self.session.commit()
        return await self._comment_response(row)

    def _task_response(self, row: InvestigationTask) -> TaskResponse:
        return TaskResponse(
            id=row.id,
            case_id=row.case_id,
            title=row.title,
            description=row.description,
            assignee_id=row.assignee_id,
            created_by=row.created_by,
            priority=row.priority,
            status=row.status,
            due_date=row.due_date,
            linked_evidence_id=row.linked_evidence_id,
            linked_report_id=row.linked_report_id,
            completed_at=row.completed_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create_task(
        self,
        case_id: UUID,
        *,
        title: str,
        description: str | None,
        assignee_id: UUID | None,
        priority: str,
        due_date: datetime | None,
        linked_evidence_id: UUID | None,
        linked_report_id: UUID | None,
        principal: AuthenticatedPrincipal | None,
    ) -> TaskResponse:
        await self._require_case(case_id)
        if principal is None:
            raise CollaborationForbiddenError("Authentication is required.")
        if assignee_id is not None:
            await self._require_user(assignee_id)
        row = InvestigationTask(
            case_id=case_id,
            title=title,
            description=description,
            assignee_id=assignee_id,
            created_by=principal.user_id,
            priority=priority,
            status=TaskStatus.OPEN.value,
            due_date=due_date,
            linked_evidence_id=linked_evidence_id,
            linked_report_id=linked_report_id,
        )
        await self.repository.add(row)
        await self.session.flush()
        if assignee_id is not None:
            await create_notification(
                self.session,
                user_id=assignee_id,
                case_id=case_id,
                kind=NotificationKind.ASSIGNMENT.value,
                title="Task assigned",
                body=f"Task assigned: {title}",
                payload={"task_id": str(row.id)},
            )
        await record_activity(
            self.session,
            case_id=case_id,
            actor_id=principal.user_id,
            actor_username=principal.username,
            action="task.created",
            summary=f"Task created: {title}",
            details={"task_id": str(row.id)},
        )
        await self.session.commit()
        return self._task_response(row)

    async def list_tasks(self, case_id: UUID) -> TaskListResponse:
        await self._require_case(case_id)
        rows = await self.repository.list_tasks(case_id)
        items = [self._task_response(row) for row in rows]
        return TaskListResponse(items=items, total=len(items))

    async def update_task(
        self,
        task_id: UUID,
        *,
        updates: dict[str, Any],
        principal: AuthenticatedPrincipal | None,
    ) -> TaskResponse:
        row = await self.repository.get_task(task_id)
        if row is None:
            raise ResourceNotFoundError("The task was not found.")
        for key, value in updates.items():
            if value is not None or key in {"description", "assignee_id", "due_date"}:
                setattr(row, key, value)
        if updates.get("status") == TaskStatus.COMPLETED.value:
            row.completed_at = datetime.now(UTC)
            if row.assignee_id is not None:
                await create_notification(
                    self.session,
                    user_id=row.created_by,
                    case_id=row.case_id,
                    kind=NotificationKind.TASK_COMPLETED.value,
                    title="Task completed",
                    body=f"Task completed: {row.title}",
                    payload={"task_id": str(row.id)},
                )
            await record_activity(
                self.session,
                case_id=row.case_id,
                actor_id=principal.user_id if principal else None,
                actor_username=principal.username if principal else "system",
                action="task.completed",
                summary=f"Task completed: {row.title}",
                details={"task_id": str(row.id)},
            )
        elif updates.get("status") == TaskStatus.REOPENED.value:
            row.completed_at = None
        await self.session.commit()
        return self._task_response(row)

    async def delete_task(self, task_id: UUID) -> None:
        row = await self.repository.get_task(task_id)
        if row is None:
            raise ResourceNotFoundError("The task was not found.")
        await self.session.delete(row)
        await self.session.commit()

    def _review_response(self, row: InvestigationReview) -> ReviewResponse:
        return ReviewResponse(
            id=row.id,
            case_id=row.case_id,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            state=row.state,
            requested_by=row.requested_by,
            reviewer_id=row.reviewer_id,
            decision=row.decision,
            comments=row.comments,
            decided_at=row.decided_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create_review(
        self,
        *,
        case_id: UUID,
        resource_type: str,
        resource_id: str,
        reviewer_id: UUID | None,
        comments: str | None,
        principal: AuthenticatedPrincipal | None,
    ) -> ReviewResponse:
        await self._require_case(case_id)
        if principal is None:
            raise CollaborationForbiddenError("Authentication is required.")
        row = InvestigationReview(
            case_id=case_id,
            resource_type=resource_type,
            resource_id=resource_id,
            state=ReviewState.UNDER_REVIEW.value,
            requested_by=principal.user_id,
            reviewer_id=reviewer_id,
            comments=comments,
        )
        await self.repository.add(row)
        await self.session.flush()
        if reviewer_id is not None:
            await create_notification(
                self.session,
                user_id=reviewer_id,
                case_id=case_id,
                kind=NotificationKind.APPROVAL_REQUEST.value,
                title="Review requested",
                body="A review was requested.",
                payload={"review_id": str(row.id)},
            )
        await record_activity(
            self.session,
            case_id=case_id,
            actor_id=principal.user_id,
            actor_username=principal.username,
            action="review.requested",
            summary="Review requested",
            details={"review_id": str(row.id)},
        )
        await self.session.commit()
        return self._review_response(row)

    async def update_review(
        self,
        review_id: UUID,
        *,
        decision: str,
        comments: str | None,
        reviewer_id: UUID | None,
        principal: AuthenticatedPrincipal | None,
    ) -> ReviewResponse:
        row = await self.repository.get_review(review_id)
        if row is None:
            raise ResourceNotFoundError("The review was not found.")
        row.state = apply_review_decision(row.state, decision)
        row.decision = decision
        row.comments = comments
        row.reviewer_id = (
            reviewer_id
            or (principal.user_id if principal else None)
            or row.reviewer_id
        )
        row.decided_at = datetime.now(UTC)
        await create_notification(
            self.session,
            user_id=row.requested_by,
            case_id=row.case_id,
            kind=NotificationKind.REVIEW_COMPLETED.value,
            title="Review completed",
            body=f"Review decision: {decision}",
            payload={"review_id": str(row.id), "decision": decision},
        )
        await record_activity(
            self.session,
            case_id=row.case_id,
            actor_id=principal.user_id if principal else None,
            actor_username=principal.username if principal else "system",
            action="review.completed",
            summary=f"Review {decision}",
            details={"review_id": str(row.id), "decision": decision},
        )
        await self.session.commit()
        return self._review_response(row)

    async def list_notifications(
        self, principal: AuthenticatedPrincipal,
    ) -> NotificationListResponse:
        rows = await self.repository.list_notifications(principal.user_id)
        items = [
            NotificationResponse(
                id=row.id,
                user_id=row.user_id,
                case_id=row.case_id,
                kind=row.kind,
                title=row.title,
                body=row.body,
                status=row.status,
                payload=dict(row.payload_json or {}),
                created_at=row.created_at,
                read_at=row.read_at,
            )
            for row in rows
        ]
        unread = await self.repository.count_unread(principal.user_id)
        return NotificationListResponse(
            items=items, total=len(items), unread_count=unread,
        )

    async def update_notification(
        self,
        notification_id: UUID,
        status: str,
        principal: AuthenticatedPrincipal,
    ) -> NotificationResponse:
        row = await self.repository.get_notification(notification_id)
        if row is None or row.user_id != principal.user_id:
            raise ResourceNotFoundError("The notification was not found.")
        if status not in {"unread", "read", "archived"}:
            raise CollaborationError(f"Unknown notification status: {status}")
        row.status = status
        row.read_at = datetime.now(UTC) if status == "read" else row.read_at
        await self.session.commit()
        return NotificationResponse(
            id=row.id,
            user_id=row.user_id,
            case_id=row.case_id,
            kind=row.kind,
            title=row.title,
            body=row.body,
            status=row.status,
            payload=dict(row.payload_json or {}),
            created_at=row.created_at,
            read_at=row.read_at,
        )

    async def list_activity(self, case_id: UUID) -> ActivityListResponse:
        await self._require_case(case_id)
        rows = await self.repository.list_activity(case_id)
        items = [
            ActivityResponse(
                id=row.id,
                case_id=row.case_id,
                actor_id=row.actor_id,
                actor_username=row.actor_username,
                action=row.action,
                summary=row.summary,
                details=dict(row.details_json or {}),
                created_at=row.created_at,
            )
            for row in rows
        ]
        return ActivityListResponse(items=items, total=len(items))

    async def get_workflow(self, case_id: UUID) -> WorkflowResponse:
        await self._require_case(case_id)
        row = await self.repository.get_workflow(case_id)
        if row is None:
            row = CaseWorkflowState(
                case_id=case_id,
                stage=CaseWorkflowStage.OPEN.value,
                version=1,
            )
            await self.repository.add(row)
            await self.session.commit()
        return WorkflowResponse(
            case_id=row.case_id,
            stage=row.stage,
            version=row.version,
            updated_by=row.updated_by,
            updated_at=row.updated_at,
            allowed_transitions=allowed_transitions(row.stage),
        )

    async def transition_workflow(
        self,
        case_id: UUID,
        stage: str,
        principal: AuthenticatedPrincipal | None,
    ) -> WorkflowResponse:
        await self._require_case(case_id)
        row = await self.repository.get_workflow(case_id)
        if row is None:
            row = CaseWorkflowState(
                case_id=case_id,
                stage=CaseWorkflowStage.OPEN.value,
                version=1,
            )
            await self.repository.add(row)
            await self.session.flush()
        target = assert_transition(row.stage, stage)
        previous = row.stage
        row.stage = target.value
        row.version += 1
        row.updated_by = principal.user_id if principal else None
        await record_activity(
            self.session,
            case_id=case_id,
            actor_id=principal.user_id if principal else None,
            actor_username=principal.username if principal else "system",
            action="workflow.changed",
            summary=f"Workflow moved from {previous} to {target.value}",
            details={"from": previous, "to": target.value},
        )
        await self.session.commit()
        return WorkflowResponse(
            case_id=row.case_id,
            stage=row.stage,
            version=row.version,
            updated_by=row.updated_by,
            updated_at=row.updated_at,
            allowed_transitions=allowed_transitions(row.stage),
        )
