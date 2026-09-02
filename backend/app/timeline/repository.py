"""Repository operations for investigation timelines."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.timeline import (
    InvestigationTimeline,
    TimelineConflictRecord,
    TimelineEventRecord,
)
from backend.app.timeline.models import TimelineRunStatus


class TimelineRepository:
    """Encapsulate timeline persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_timeline(self, timeline_id: UUID) -> InvestigationTimeline | None:
        return await self.session.get(InvestigationTimeline, timeline_id)

    async def get_timeline_with_details(
        self,
        timeline_id: UUID,
    ) -> InvestigationTimeline | None:
        result = await self.session.scalars(
            select(InvestigationTimeline)
            .where(InvestigationTimeline.id == timeline_id)
            .options(
                selectinload(InvestigationTimeline.events),
                selectinload(InvestigationTimeline.conflicts),
            )
        )
        return result.first()

    async def get_active_for_case(self, case_id: UUID) -> InvestigationTimeline | None:
        result = await self.session.scalars(
            select(InvestigationTimeline).where(
                InvestigationTimeline.case_id == case_id,
                InvestigationTimeline.status.in_(
                    [TimelineRunStatus.QUEUED, TimelineRunStatus.RUNNING]
                ),
            )
        )
        return result.first()

    async def get_latest_for_case(self, case_id: UUID) -> InvestigationTimeline | None:
        result = await self.session.scalars(
            select(InvestigationTimeline)
            .where(InvestigationTimeline.case_id == case_id)
            .order_by(InvestigationTimeline.created_at.desc())
            .limit(1)
            .options(
                selectinload(InvestigationTimeline.events),
                selectinload(InvestigationTimeline.conflicts),
            )
        )
        return result.first()

    async def list_for_case(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[InvestigationTimeline], int]:
        filters = [InvestigationTimeline.case_id == case_id]
        total = await self.session.scalar(
            select(func.count()).select_from(InvestigationTimeline).where(*filters)
        )
        result = await self.session.scalars(
            select(InvestigationTimeline)
            .where(*filters)
            .order_by(InvestigationTimeline.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def list_events_for_evidence(
        self,
        timeline_id: UUID,
        evidence_id: UUID,
    ) -> list[TimelineEventRecord]:
        result = await self.session.scalars(
            select(TimelineEventRecord)
            .where(
                TimelineEventRecord.timeline_id == timeline_id,
                TimelineEventRecord.evidence_id == evidence_id,
            )
            .order_by(TimelineEventRecord.normalized_timestamp.asc())
        )
        return list(result)

    async def list_conflicts(self, timeline_id: UUID) -> list[TimelineConflictRecord]:
        result = await self.session.scalars(
            select(TimelineConflictRecord)
            .where(TimelineConflictRecord.timeline_id == timeline_id)
            .order_by(TimelineConflictRecord.conflict_type.asc())
        )
        return list(result)

    async def add_timeline(
        self, timeline: InvestigationTimeline
    ) -> InvestigationTimeline:
        self.session.add(timeline)
        await self.session.flush()
        return timeline

    async def add_event(self, event: TimelineEventRecord) -> TimelineEventRecord:
        self.session.add(event)
        await self.session.flush()
        return event

    async def add_conflict(
        self,
        conflict: TimelineConflictRecord,
    ) -> TimelineConflictRecord:
        self.session.add(conflict)
        await self.session.flush()
        return conflict

    async def delete_timeline(self, timeline_id: UUID) -> None:
        timeline = await self.get_timeline(timeline_id)
        if timeline is not None:
            await self.session.delete(timeline)
            await self.session.flush()
