"""Repository operations for AI video forensic analysis."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.domain.processing import ArtifactType
from backend.app.models.processing import Artifact
from backend.app.models.video_ai import (
    VideoAIFinding,
    VideoAIFindingRegion,
    VideoAnalysisRun,
)


class VideoAnalysisRepository:
    """Encapsulate AI video analysis persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(self, analysis_id: UUID) -> VideoAnalysisRun | None:
        return await self.session.get(VideoAnalysisRun, analysis_id)

    async def get_run_with_findings(
        self,
        analysis_id: UUID,
    ) -> VideoAnalysisRun | None:
        result = await self.session.scalars(
            select(VideoAnalysisRun)
            .where(VideoAnalysisRun.id == analysis_id)
            .options(
                selectinload(VideoAnalysisRun.findings).selectinload(
                    VideoAIFinding.regions
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
    ) -> tuple[list[VideoAnalysisRun], int]:
        filters = [VideoAnalysisRun.evidence_id == evidence_id]
        total = await self.session.scalar(
            select(func.count()).select_from(VideoAnalysisRun).where(*filters)
        )
        result = await self.session.scalars(
            select(VideoAnalysisRun)
            .where(*filters)
            .order_by(VideoAnalysisRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def add_run(self, run: VideoAnalysisRun) -> VideoAnalysisRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_finding(self, finding: VideoAIFinding) -> VideoAIFinding:
        self.session.add(finding)
        await self.session.flush()
        return finding

    async def add_region(self, region: VideoAIFindingRegion) -> VideoAIFindingRegion:
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
    ) -> tuple[list[VideoAIFinding], int]:
        filters = [VideoAIFinding.evidence_id == evidence_id]
        if detector:
            filters.append(VideoAIFinding.detector == detector)
        total = await self.session.scalar(
            select(func.count()).select_from(VideoAIFinding).where(*filters)
        )
        result = await self.session.scalars(
            select(VideoAIFinding)
            .where(*filters)
            .options(selectinload(VideoAIFinding.regions))
            .order_by(VideoAIFinding.created_at.desc())
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
            ArtifactType.AI_VIDEO_FRAME,
            ArtifactType.AI_VIDEO_HEATMAP,
            ArtifactType.AI_VIDEO_MASK,
            ArtifactType.AI_VIDEO_OVERLAY,
            ArtifactType.AI_VIDEO_PREDICTION,
            ArtifactType.AI_VIDEO_TIMELINE,
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
