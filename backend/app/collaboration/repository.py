"""Persistence helpers for collaboration entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.case import Case
from backend.app.models.collaboration import (
    ActivityLog,
    CaseMember,
    CaseWorkflowState,
    EvidenceAssignment,
    InvestigationComment,
    InvestigationMention,
    InvestigationReview,
    InvestigationTask,
    Notification,
)
from backend.app.models.evidence import Evidence
from backend.app.models.user import User


class CollaborationRepository:
    """Query helper for collaboration tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_case(self, case_id: UUID) -> Case | None:
        result = await self.session.execute(select(Case).where(Case.id == case_id))
        return result.scalar_one_or_none()

    async def get_evidence(self, evidence_id: UUID) -> Evidence | None:
        result = await self.session.execute(
            select(Evidence).where(Evidence.id == evidence_id)
        )
        return result.scalar_one_or_none()

    async def get_user(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(func.lower(User.username) == username.lower())
        )
        return result.scalar_one_or_none()

    async def list_members(self, case_id: UUID) -> list[CaseMember]:
        result = await self.session.execute(
            select(CaseMember)
            .where(CaseMember.case_id == case_id)
            .order_by(CaseMember.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_member(
        self, case_id: UUID, member_id: UUID,
    ) -> CaseMember | None:
        result = await self.session.execute(
            select(CaseMember).where(
                CaseMember.id == member_id,
                CaseMember.case_id == case_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_member_by_user(
        self, case_id: UUID, user_id: UUID,
    ) -> CaseMember | None:
        result = await self.session.execute(
            select(CaseMember).where(
                CaseMember.case_id == case_id,
                CaseMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_owners(self, case_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count(CaseMember.id)).where(
                CaseMember.case_id == case_id,
                CaseMember.role == "owner",
            )
        )
        return int(result.scalar_one())

    async def list_assignments(
        self, evidence_id: UUID,
    ) -> list[EvidenceAssignment]:
        result = await self.session.execute(
            select(EvidenceAssignment)
            .where(EvidenceAssignment.evidence_id == evidence_id)
            .order_by(EvidenceAssignment.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_comments(
        self,
        *,
        resource_type: str,
        resource_id: str,
    ) -> list[InvestigationComment]:
        result = await self.session.execute(
            select(InvestigationComment)
            .where(
                InvestigationComment.resource_type == resource_type,
                InvestigationComment.resource_id == resource_id,
            )
            .order_by(InvestigationComment.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_comment(
        self, comment_id: UUID,
    ) -> InvestigationComment | None:
        result = await self.session.execute(
            select(InvestigationComment).where(
                InvestigationComment.id == comment_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_mentions(
        self, comment_id: UUID,
    ) -> list[InvestigationMention]:
        result = await self.session.execute(
            select(InvestigationMention).where(
                InvestigationMention.comment_id == comment_id,
            )
        )
        return list(result.scalars().all())

    async def list_tasks(self, case_id: UUID) -> list[InvestigationTask]:
        result = await self.session.execute(
            select(InvestigationTask)
            .where(InvestigationTask.case_id == case_id)
            .order_by(InvestigationTask.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_task(self, task_id: UUID) -> InvestigationTask | None:
        result = await self.session.execute(
            select(InvestigationTask).where(InvestigationTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_review(
        self, review_id: UUID,
    ) -> InvestigationReview | None:
        result = await self.session.execute(
            select(InvestigationReview).where(
                InvestigationReview.id == review_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_notifications(
        self, user_id: UUID,
    ) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_notification(
        self, notification_id: UUID,
    ) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def count_unread(self, user_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.status == "unread",
            )
        )
        return int(result.scalar_one())

    async def list_activity(self, case_id: UUID) -> list[ActivityLog]:
        result = await self.session.execute(
            select(ActivityLog)
            .where(ActivityLog.case_id == case_id)
            .order_by(ActivityLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_workflow(
        self, case_id: UUID,
    ) -> CaseWorkflowState | None:
        result = await self.session.execute(
            select(CaseWorkflowState).where(
                CaseWorkflowState.case_id == case_id,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, entity: object) -> None:
        self.session.add(entity)
