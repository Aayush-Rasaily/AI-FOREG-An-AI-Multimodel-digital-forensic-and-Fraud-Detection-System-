"""Repository operations for entity resolution."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.entities.models import EntityRunStatus
from backend.app.models.entity import (
    EntityRelationshipRecord,
    EntityResolutionRun,
    EntitySupportRecord,
    InvestigationEntityRecord,
)


class EntityRepository:
    """Encapsulate entity-resolution persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(self, run_id: UUID) -> EntityResolutionRun | None:
        return await self.session.get(EntityResolutionRun, run_id)

    async def get_run_with_details(
        self,
        run_id: UUID,
    ) -> EntityResolutionRun | None:
        result = await self.session.scalars(
            select(EntityResolutionRun)
            .where(EntityResolutionRun.id == run_id)
            .options(
                selectinload(EntityResolutionRun.entities).selectinload(
                    InvestigationEntityRecord.support_records
                ),
                selectinload(EntityResolutionRun.relationships).selectinload(
                    EntityRelationshipRecord.support_records
                ),
            )
        )
        return result.first()

    async def get_active_for_case(self, case_id: UUID) -> EntityResolutionRun | None:
        result = await self.session.scalars(
            select(EntityResolutionRun).where(
                EntityResolutionRun.case_id == case_id,
                EntityResolutionRun.status.in_(
                    [EntityRunStatus.QUEUED, EntityRunStatus.RUNNING]
                ),
            )
        )
        return result.first()

    async def get_latest_for_case(self, case_id: UUID) -> EntityResolutionRun | None:
        result = await self.session.scalars(
            select(EntityResolutionRun)
            .where(EntityResolutionRun.case_id == case_id)
            .order_by(EntityResolutionRun.created_at.desc())
            .limit(1)
            .options(
                selectinload(EntityResolutionRun.entities).selectinload(
                    InvestigationEntityRecord.support_records
                ),
                selectinload(EntityResolutionRun.relationships).selectinload(
                    EntityRelationshipRecord.support_records
                ),
            )
        )
        return result.first()

    async def list_for_case(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[EntityResolutionRun], int]:
        filters = [EntityResolutionRun.case_id == case_id]
        total = await self.session.scalar(
            select(func.count()).select_from(EntityResolutionRun).where(*filters)
        )
        result = await self.session.scalars(
            select(EntityResolutionRun)
            .where(*filters)
            .order_by(EntityResolutionRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def get_entity(
        self,
        entity_id: UUID,
    ) -> InvestigationEntityRecord | None:
        result = await self.session.scalars(
            select(InvestigationEntityRecord)
            .where(InvestigationEntityRecord.id == entity_id)
            .options(selectinload(InvestigationEntityRecord.support_records))
        )
        return result.first()

    async def list_relationships_for_entity(
        self,
        entity: InvestigationEntityRecord,
    ) -> list[EntityRelationshipRecord]:
        result = await self.session.scalars(
            select(EntityRelationshipRecord)
            .where(
                EntityRelationshipRecord.analysis_run_id == entity.analysis_run_id,
                or_(
                    EntityRelationshipRecord.source_canonical_id == entity.canonical_id,
                    EntityRelationshipRecord.target_canonical_id == entity.canonical_id,
                ),
            )
            .order_by(EntityRelationshipRecord.confidence.desc())
            .options(selectinload(EntityRelationshipRecord.support_records))
        )
        return list(result)

    async def add_run(self, run: EntityResolutionRun) -> EntityResolutionRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_entity(
        self,
        record: InvestigationEntityRecord,
    ) -> InvestigationEntityRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def add_relationship(
        self,
        record: EntityRelationshipRecord,
    ) -> EntityRelationshipRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def add_support(
        self,
        record: EntitySupportRecord,
    ) -> EntitySupportRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def delete_run(self, run_id: UUID) -> None:
        run = await self.get_run(run_id)
        if run is not None:
            await self.session.delete(run)
            await self.session.flush()
