"""Repository operations for case intelligence."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.case_intelligence.models import CaseIntelligenceRunStatus
from backend.app.models.case_intelligence import (
    CaseConflictRecord,
    CaseEvidenceParticipationRecord,
    CaseIntelligenceRun,
    CaseRelationshipRecord,
    CaseTimelineEventRecord,
)


class CaseIntelligenceRepository:
    """Encapsulate case intelligence persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(self, analysis_id: UUID) -> CaseIntelligenceRun | None:
        return await self.session.get(CaseIntelligenceRun, analysis_id)

    async def get_active_for_case(self, case_id: UUID) -> CaseIntelligenceRun | None:
        result = await self.session.scalars(
            select(CaseIntelligenceRun).where(
                CaseIntelligenceRun.case_id == case_id,
                CaseIntelligenceRun.status.in_(
                    [
                        CaseIntelligenceRunStatus.QUEUED,
                        CaseIntelligenceRunStatus.RUNNING,
                    ]
                ),
            )
        )
        return result.first()

    async def get_run_with_details(
        self,
        analysis_id: UUID,
    ) -> CaseIntelligenceRun | None:
        result = await self.session.scalars(
            select(CaseIntelligenceRun)
            .where(CaseIntelligenceRun.id == analysis_id)
            .options(
                selectinload(CaseIntelligenceRun.participations),
                selectinload(CaseIntelligenceRun.relationships),
                selectinload(CaseIntelligenceRun.conflicts),
                selectinload(CaseIntelligenceRun.timeline_events),
            )
        )
        return result.first()

    async def get_latest_for_case(
        self,
        case_id: UUID,
    ) -> CaseIntelligenceRun | None:
        result = await self.session.scalars(
            select(CaseIntelligenceRun)
            .where(CaseIntelligenceRun.case_id == case_id)
            .order_by(CaseIntelligenceRun.created_at.desc())
            .limit(1)
            .options(
                selectinload(CaseIntelligenceRun.participations),
                selectinload(CaseIntelligenceRun.relationships),
                selectinload(CaseIntelligenceRun.conflicts),
                selectinload(CaseIntelligenceRun.timeline_events),
            )
        )
        return result.first()

    async def list_runs_for_case(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[CaseIntelligenceRun], int]:
        filters = [CaseIntelligenceRun.case_id == case_id]
        total = await self.session.scalar(
            select(func.count()).select_from(CaseIntelligenceRun).where(*filters)
        )
        result = await self.session.scalars(
            select(CaseIntelligenceRun)
            .where(*filters)
            .order_by(CaseIntelligenceRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def add_run(self, run: CaseIntelligenceRun) -> CaseIntelligenceRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_participation(
        self,
        record: CaseEvidenceParticipationRecord,
    ) -> CaseEvidenceParticipationRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def add_relationship(
        self,
        record: CaseRelationshipRecord,
    ) -> CaseRelationshipRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def add_conflict(
        self,
        record: CaseConflictRecord,
    ) -> CaseConflictRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def add_timeline_event(
        self,
        record: CaseTimelineEventRecord,
    ) -> CaseTimelineEventRecord:
        self.session.add(record)
        await self.session.flush()
        return record
