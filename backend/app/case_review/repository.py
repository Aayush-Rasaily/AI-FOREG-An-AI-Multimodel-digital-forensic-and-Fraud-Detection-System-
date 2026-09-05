"""Persistence repository for case review."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.case import Case
from backend.app.models.case_review import (
    CaseReviewApproval,
    CaseReviewChecklist,
    CaseReviewChecklistItem,
    CaseReviewRun,
    CaseReviewValidationRecord,
)


class CaseReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def add_run(self, run: CaseReviewRun) -> CaseReviewRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_checklist(
        self,
        checklist: CaseReviewChecklist,
    ) -> CaseReviewChecklist:
        self.session.add(checklist)
        await self.session.flush()
        return checklist

    async def add_items(self, rows: list[CaseReviewChecklistItem]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def add_validation(
        self,
        row: CaseReviewValidationRecord,
    ) -> CaseReviewValidationRecord:
        self.session.add(row)
        await self.session.flush()
        return row

    async def add_approval(
        self,
        row: CaseReviewApproval,
    ) -> CaseReviewApproval:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_run(self, run_id: UUID) -> CaseReviewRun | None:
        return await self.session.get(CaseReviewRun, run_id)

    async def get_latest_run(self, case_id: UUID) -> CaseReviewRun | None:
        result = await self.session.execute(
            select(CaseReviewRun)
            .where(CaseReviewRun.case_id == case_id)
            .order_by(CaseReviewRun.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def list_runs(
        self,
        case_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CaseReviewRun], int]:
        total = await self.session.scalar(
            select(func.count())
            .select_from(CaseReviewRun)
            .where(CaseReviewRun.case_id == case_id)
        )
        result = await self.session.execute(
            select(CaseReviewRun)
            .where(CaseReviewRun.case_id == case_id)
            .order_by(CaseReviewRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)

    async def get_checklist_for_run(
        self,
        run_id: UUID,
    ) -> CaseReviewChecklist | None:
        result = await self.session.execute(
            select(CaseReviewChecklist)
            .where(CaseReviewChecklist.run_id == run_id)
            .order_by(CaseReviewChecklist.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def items_for_run(
        self,
        run_id: UUID,
    ) -> list[CaseReviewChecklistItem]:
        result = await self.session.execute(
            select(CaseReviewChecklistItem).where(
                CaseReviewChecklistItem.run_id == run_id
            )
        )
        rows = list(result.scalars().all())
        rows.sort(key=lambda item: (item.item_code, item.item_key))
        return rows

    async def get_item(
        self,
        item_id: UUID,
    ) -> CaseReviewChecklistItem | None:
        return await self.session.get(CaseReviewChecklistItem, item_id)

    async def approvals_for_run(
        self,
        run_id: UUID,
    ) -> list[CaseReviewApproval]:
        result = await self.session.execute(
            select(CaseReviewApproval).where(CaseReviewApproval.run_id == run_id)
        )
        rows = list(result.scalars().all())
        rows.sort(key=lambda item: (item.approver_role, item.created_at.isoformat()))
        return rows

    async def list_approvals_for_case(
        self,
        case_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[CaseReviewApproval], int]:
        total = await self.session.scalar(
            select(func.count())
            .select_from(CaseReviewApproval)
            .where(CaseReviewApproval.case_id == case_id)
        )
        result = await self.session.execute(
            select(CaseReviewApproval)
            .where(CaseReviewApproval.case_id == case_id)
            .order_by(CaseReviewApproval.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)
