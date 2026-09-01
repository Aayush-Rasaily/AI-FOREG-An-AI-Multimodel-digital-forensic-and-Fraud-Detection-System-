"""Repository operations for AI image forensic analysis."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.domain.processing import ArtifactType
from backend.app.models.image_ai import (
    ImageAIFinding,
    ImageAIFindingRegion,
    ImageAnalysisRun,
)
from backend.app.models.processing import Artifact


class ImageAnalysisRepository:
    """Encapsulate AI image analysis persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(self, analysis_id: UUID) -> ImageAnalysisRun | None:
        return await self.session.get(ImageAnalysisRun, analysis_id)

    async def get_run_with_findings(
        self,
        analysis_id: UUID,
    ) -> ImageAnalysisRun | None:
        result = await self.session.scalars(
            select(ImageAnalysisRun)
            .where(ImageAnalysisRun.id == analysis_id)
            .options(
                selectinload(ImageAnalysisRun.findings).selectinload(
                    ImageAIFinding.regions
                ),
            )
        )
        return result.first()

    async def list_runs_for_evidence(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[ImageAnalysisRun], int]:
        filters = [ImageAnalysisRun.evidence_id == evidence_id]
        total = await self.session.scalar(
            select(func.count()).select_from(ImageAnalysisRun).where(*filters)
        )
        result = await self.session.scalars(
            select(ImageAnalysisRun)
            .where(*filters)
            .order_by(ImageAnalysisRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def latest_run_for_evidence(
        self,
        evidence_id: UUID,
    ) -> ImageAnalysisRun | None:
        result = await self.session.scalars(
            select(ImageAnalysisRun)
            .where(ImageAnalysisRun.evidence_id == evidence_id)
            .order_by(ImageAnalysisRun.created_at.desc())
            .limit(1)
        )
        return result.first()

    async def add_run(self, run: ImageAnalysisRun) -> ImageAnalysisRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_finding(self, finding: ImageAIFinding) -> ImageAIFinding:
        self.session.add(finding)
        await self.session.flush()
        return finding

    async def add_region(self, region: ImageAIFindingRegion) -> ImageAIFindingRegion:
        self.session.add(region)
        await self.session.flush()
        return region

    async def list_findings_for_evidence(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
        detector: str | None = None,
    ) -> tuple[list[ImageAIFinding], int]:
        filters = [ImageAIFinding.evidence_id == evidence_id]
        if detector:
            filters.append(ImageAIFinding.detector == detector)
        total = await self.session.scalar(
            select(func.count()).select_from(ImageAIFinding).where(*filters)
        )
        result = await self.session.scalars(
            select(ImageAIFinding)
            .where(*filters)
            .options(selectinload(ImageAIFinding.regions))
            .order_by(ImageAIFinding.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def list_visualization_artifacts(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Artifact], int]:
        artifact_types = (
            ArtifactType.AI_IMAGE_HEATMAP,
            ArtifactType.AI_IMAGE_MASK,
            ArtifactType.AI_IMAGE_OVERLAY,
            ArtifactType.AI_IMAGE_PREDICTION,
        )
        filters = [
            Artifact.evidence_id == evidence_id,
            Artifact.artifact_type.in_(artifact_types),
        ]
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
