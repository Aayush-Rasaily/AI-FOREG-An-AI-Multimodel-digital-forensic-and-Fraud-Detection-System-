"""Repository operations for multimodal fusion."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.fusion import (
    FusionAnalysisRun,
    FusionConflictRecord,
    JuryAssessmentRecord,
)


class FusionRepository:
    """Encapsulate fusion persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(self, analysis_id: UUID) -> FusionAnalysisRun | None:
        return await self.session.get(FusionAnalysisRun, analysis_id)

    async def get_run_with_details(
        self,
        analysis_id: UUID,
    ) -> FusionAnalysisRun | None:
        result = await self.session.scalars(
            select(FusionAnalysisRun)
            .where(FusionAnalysisRun.id == analysis_id)
            .options(
                selectinload(FusionAnalysisRun.jury_assessments),
                selectinload(FusionAnalysisRun.conflicts),
            )
        )
        return result.first()

    async def get_latest_for_evidence(
        self,
        evidence_id: UUID,
    ) -> FusionAnalysisRun | None:
        result = await self.session.scalars(
            select(FusionAnalysisRun)
            .where(FusionAnalysisRun.evidence_id == evidence_id)
            .order_by(FusionAnalysisRun.created_at.desc())
            .limit(1)
            .options(
                selectinload(FusionAnalysisRun.jury_assessments),
                selectinload(FusionAnalysisRun.conflicts),
            )
        )
        return result.first()

    async def list_runs_for_evidence(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[FusionAnalysisRun], int]:
        filters = [FusionAnalysisRun.evidence_id == evidence_id]
        total = await self.session.scalar(
            select(func.count()).select_from(FusionAnalysisRun).where(*filters)
        )
        result = await self.session.scalars(
            select(FusionAnalysisRun)
            .where(*filters)
            .order_by(FusionAnalysisRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def add_run(self, run: FusionAnalysisRun) -> FusionAnalysisRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_jury_assessment(
        self,
        record: JuryAssessmentRecord,
    ) -> JuryAssessmentRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def add_conflict(
        self,
        record: FusionConflictRecord,
    ) -> FusionConflictRecord:
        self.session.add(record)
        await self.session.flush()
        return record
