"""Repository operations for AI audio forensic analysis."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.domain.processing import ArtifactType
from backend.app.models.audio_ai import (
    AudioAIFinding,
    AudioAIFindingRegion,
    AudioAnalysisRun,
)
from backend.app.models.processing import Artifact


class AudioAnalysisRepository:
    """Encapsulate AI audio analysis persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(self, analysis_id: UUID) -> AudioAnalysisRun | None:
        return await self.session.get(AudioAnalysisRun, analysis_id)

    async def get_run_with_findings(
        self,
        analysis_id: UUID,
    ) -> AudioAnalysisRun | None:
        result = await self.session.scalars(
            select(AudioAnalysisRun)
            .where(AudioAnalysisRun.id == analysis_id)
            .options(
                selectinload(AudioAnalysisRun.findings).selectinload(
                    AudioAIFinding.regions
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
    ) -> tuple[list[AudioAnalysisRun], int]:
        filters = [AudioAnalysisRun.evidence_id == evidence_id]
        total = await self.session.scalar(
            select(func.count()).select_from(AudioAnalysisRun).where(*filters)
        )
        result = await self.session.scalars(
            select(AudioAnalysisRun)
            .where(*filters)
            .order_by(AudioAnalysisRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def add_run(self, run: AudioAnalysisRun) -> AudioAnalysisRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_finding(self, finding: AudioAIFinding) -> AudioAIFinding:
        self.session.add(finding)
        await self.session.flush()
        return finding

    async def add_region(self, region: AudioAIFindingRegion) -> AudioAIFindingRegion:
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
    ) -> tuple[list[AudioAIFinding], int]:
        filters = [AudioAIFinding.evidence_id == evidence_id]
        if detector:
            filters.append(AudioAIFinding.detector == detector)
        total = await self.session.scalar(
            select(func.count()).select_from(AudioAIFinding).where(*filters)
        )
        result = await self.session.scalars(
            select(AudioAIFinding)
            .where(*filters)
            .options(selectinload(AudioAIFinding.regions))
            .order_by(AudioAIFinding.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def list_audio_artifacts(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Artifact], int]:
        artifact_types = (
            ArtifactType.AI_AUDIO_WAVEFORM,
            ArtifactType.AI_AUDIO_SPECTROGRAM,
            ArtifactType.AI_AUDIO_FEATURES,
            ArtifactType.AI_AUDIO_TIMELINE,
            ArtifactType.AI_AUDIO_PREDICTION,
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
