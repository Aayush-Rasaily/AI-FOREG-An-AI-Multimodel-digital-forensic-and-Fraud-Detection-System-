"""Repository operations for AI model records and inference jobs."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.ai import AIModelRecord, InferenceJob, InferenceLog


class AIRepository:
    """Encapsulate AI infrastructure persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_models(
        self,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[AIModelRecord], int]:
        total = await self.session.scalar(
            select(func.count()).select_from(AIModelRecord)
        )
        result = await self.session.scalars(
            select(AIModelRecord)
            .order_by(AIModelRecord.name.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def get_model_by_name(self, name: str) -> AIModelRecord | None:
        result = await self.session.scalars(
            select(AIModelRecord).where(AIModelRecord.name == name)
        )
        return result.first()

    async def get_model(self, model_id: UUID) -> AIModelRecord | None:
        return await self.session.get(AIModelRecord, model_id)

    async def upsert_model(self, record: AIModelRecord) -> AIModelRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def list_jobs(
        self,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[InferenceJob], int]:
        total = await self.session.scalar(
            select(func.count()).select_from(InferenceJob)
        )
        result = await self.session.scalars(
            select(InferenceJob)
            .options(selectinload(InferenceJob.logs))
            .order_by(InferenceJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def get_job(self, job_id: UUID) -> InferenceJob | None:
        result = await self.session.scalars(
            select(InferenceJob)
            .where(InferenceJob.id == job_id)
            .options(selectinload(InferenceJob.logs))
        )
        return result.first()

    async def add_job(self, job: InferenceJob) -> InferenceJob:
        self.session.add(job)
        await self.session.flush()
        return job

    async def add_log(self, log: InferenceLog) -> InferenceLog:
        self.session.add(log)
        await self.session.flush()
        return log
