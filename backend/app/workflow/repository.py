"""Persistence helpers for investigation workflow entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.case import Case
from backend.app.models.evidence import Evidence
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.user import User
from backend.app.models.workflow import (
    InvestigationWorkflow,
    WorkflowMilestone,
    WorkflowNote,
    WorkflowNotification,
    WorkflowReview,
    WorkflowTask,
)


class WorkflowRepository:
    """Data-access layer for Phase 8E workflow tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: object) -> None:
        self.session.add(row)

    async def get_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def get_user(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_evidence(self, evidence_id: UUID) -> Evidence | None:
        return await self.session.get(Evidence, evidence_id)

    async def get_report(self, report_id: UUID) -> ForensicReport | None:
        return await self.session.get(ForensicReport, report_id)

    async def get_workflow_by_case(
        self, case_id: UUID,
    ) -> InvestigationWorkflow | None:
        result = await self.session.execute(
            select(InvestigationWorkflow).where(
                InvestigationWorkflow.case_id == case_id
            )
        )
        return result.scalar_one_or_none()

    async def get_workflow(
        self, workflow_id: UUID,
    ) -> InvestigationWorkflow | None:
        return await self.session.get(InvestigationWorkflow, workflow_id)

    async def get_task(self, task_id: UUID) -> WorkflowTask | None:
        return await self.session.get(WorkflowTask, task_id)

    async def list_tasks(self, case_id: UUID) -> list[WorkflowTask]:
        result = await self.session.execute(
            select(WorkflowTask)
            .where(WorkflowTask.case_id == case_id)
            .order_by(WorkflowTask.created_at.asc(), WorkflowTask.id.asc())
        )
        return list(result.scalars().all())

    async def list_notes(self, case_id: UUID) -> list[WorkflowNote]:
        result = await self.session.execute(
            select(WorkflowNote)
            .where(WorkflowNote.case_id == case_id)
            .order_by(WorkflowNote.created_at.asc(), WorkflowNote.id.asc())
        )
        return list(result.scalars().all())

    async def list_reviews(self, case_id: UUID) -> list[WorkflowReview]:
        result = await self.session.execute(
            select(WorkflowReview)
            .where(WorkflowReview.case_id == case_id)
            .order_by(WorkflowReview.created_at.asc(), WorkflowReview.id.asc())
        )
        return list(result.scalars().all())

    async def list_milestones(
        self, case_id: UUID,
    ) -> list[WorkflowMilestone]:
        result = await self.session.execute(
            select(WorkflowMilestone)
            .where(WorkflowMilestone.case_id == case_id)
            .order_by(
                WorkflowMilestone.reached_at.asc(),
                WorkflowMilestone.id.asc(),
            )
        )
        return list(result.scalars().all())

    async def get_milestone(
        self,
        workflow_id: UUID,
        milestone_type: str,
    ) -> WorkflowMilestone | None:
        result = await self.session.execute(
            select(WorkflowMilestone).where(
                WorkflowMilestone.workflow_id == workflow_id,
                WorkflowMilestone.milestone_type == milestone_type,
            )
        )
        return result.scalar_one_or_none()

    async def list_notifications(
        self, case_id: UUID,
    ) -> list[WorkflowNotification]:
        result = await self.session.execute(
            select(WorkflowNotification)
            .where(WorkflowNotification.case_id == case_id)
            .order_by(
                WorkflowNotification.created_at.asc(),
                WorkflowNotification.id.asc(),
            )
        )
        return list(result.scalars().all())

    async def count_evidence(self, case_id: UUID) -> int:
        result = await self.session.execute(
            select(Evidence.id).where(Evidence.case_id == case_id)
        )
        return len(list(result.scalars().all()))

    async def count_reports(self, case_id: UUID) -> int:
        result = await self.session.execute(
            select(ForensicReport.id).where(ForensicReport.case_id == case_id)
        )
        return len(list(result.scalars().all()))
