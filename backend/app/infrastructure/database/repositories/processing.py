"""Repositories for processing jobs and derived artifacts."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain.processing import (
    ArtifactType,
    ProcessingJobStatus,
    ProcessingJobType,
)
from backend.app.models.processing import Artifact, ProcessingJob


class ProcessingJobRepository:
    """Encapsulate bounded processing-job queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, job_id: UUID) -> ProcessingJob | None:
        """Return a job by internal identifier."""

        return await self.session.get(ProcessingJob, job_id)

    async def get_active(
        self,
        evidence_id: UUID,
        job_type: ProcessingJobType,
    ) -> ProcessingJob | None:
        """Return an active job for an evidence/type pair."""

        return await self.session.scalar(
            select(ProcessingJob)
            .where(
                ProcessingJob.evidence_id == evidence_id,
                ProcessingJob.job_type == job_type,
                ProcessingJob.status.in_(
                    [
                        ProcessingJobStatus.QUEUED,
                        ProcessingJobStatus.RUNNING,
                    ]
                ),
            )
            .with_for_update()
        )

    async def list_for_evidence(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[ProcessingJob], int]:
        """Return a bounded newest-first job page."""

        total = await self.session.scalar(
            select(func.count())
            .select_from(ProcessingJob)
            .where(ProcessingJob.evidence_id == evidence_id)
        )
        result = await self.session.scalars(
            select(ProcessingJob)
            .where(ProcessingJob.evidence_id == evidence_id)
            .order_by(ProcessingJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def latest_for_evidence(
        self,
        evidence_id: UUID,
        job_type: ProcessingJobType,
    ) -> ProcessingJob | None:
        """Return the newest job for an evidence/type pair."""

        return await self.session.scalar(
            select(ProcessingJob)
            .where(
                ProcessingJob.evidence_id == evidence_id,
                ProcessingJob.job_type == job_type,
            )
            .order_by(ProcessingJob.created_at.desc())
            .limit(1)
        )

    async def add(self, job: ProcessingJob) -> ProcessingJob:
        """Stage and flush a processing job."""

        self.session.add(job)
        await self.session.flush()
        return job


class ArtifactRepository:
    """Encapsulate derived artifact queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_evidence(
        self,
        evidence_id: UUID,
        *,
        artifact_type: ArtifactType | None = None,
        artifact_types: Sequence[ArtifactType] | None = None,
        limit: int,
        offset: int,
    ) -> tuple[list[Artifact], int]:
        """Return a bounded artifact page for one evidence item."""

        filters = [Artifact.evidence_id == evidence_id]
        if artifact_type is not None:
            filters.append(Artifact.artifact_type == artifact_type)
        if artifact_types is not None:
            filters.append(Artifact.artifact_type.in_(artifact_types))
        total = await self.session.scalar(
            select(func.count()).select_from(Artifact).where(*filters)
        )
        result = await self.session.scalars(
            select(Artifact)
            .where(*filters)
            .order_by(Artifact.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def add(self, artifact: Artifact) -> Artifact:
        """Stage and flush a derived artifact."""

        self.session.add(artifact)
        await self.session.flush()
        return artifact
