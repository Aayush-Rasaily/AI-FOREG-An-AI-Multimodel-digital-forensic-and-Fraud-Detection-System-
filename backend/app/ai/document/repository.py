"""Repository operations for AI document forensic analysis."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.domain.processing import ArtifactType
from backend.app.models.document_ai import (
    DocumentAIFinding,
    DocumentAIFindingRegion,
    DocumentAnalysisRun,
)
from backend.app.models.processing import Artifact


class DocumentAnalysisRepository:
    """Encapsulate AI document analysis persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(self, analysis_id: UUID) -> DocumentAnalysisRun | None:
        return await self.session.get(DocumentAnalysisRun, analysis_id)

    async def get_run_with_findings(
        self,
        analysis_id: UUID,
    ) -> DocumentAnalysisRun | None:
        result = await self.session.scalars(
            select(DocumentAnalysisRun)
            .where(DocumentAnalysisRun.id == analysis_id)
            .options(
                selectinload(DocumentAnalysisRun.findings).selectinload(
                    DocumentAIFinding.regions
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
    ) -> tuple[list[DocumentAnalysisRun], int]:
        filters = [DocumentAnalysisRun.evidence_id == evidence_id]
        total = await self.session.scalar(
            select(func.count()).select_from(DocumentAnalysisRun).where(*filters)
        )
        result = await self.session.scalars(
            select(DocumentAnalysisRun)
            .where(*filters)
            .order_by(DocumentAnalysisRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def latest_run_for_evidence(
        self,
        evidence_id: UUID,
    ) -> DocumentAnalysisRun | None:
        result = await self.session.scalars(
            select(DocumentAnalysisRun)
            .where(DocumentAnalysisRun.evidence_id == evidence_id)
            .order_by(DocumentAnalysisRun.created_at.desc())
            .limit(1)
        )
        return result.first()

    async def add_run(self, run: DocumentAnalysisRun) -> DocumentAnalysisRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_finding(self, finding: DocumentAIFinding) -> DocumentAIFinding:
        self.session.add(finding)
        await self.session.flush()
        return finding

    async def add_region(
        self,
        region: DocumentAIFindingRegion,
    ) -> DocumentAIFindingRegion:
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
    ) -> tuple[list[DocumentAIFinding], int]:
        filters = [DocumentAIFinding.evidence_id == evidence_id]
        if detector:
            filters.append(DocumentAIFinding.detector == detector)
        total = await self.session.scalar(
            select(func.count()).select_from(DocumentAIFinding).where(*filters)
        )
        result = await self.session.scalars(
            select(DocumentAIFinding)
            .where(*filters)
            .options(selectinload(DocumentAIFinding.regions))
            .order_by(DocumentAIFinding.created_at.desc())
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
            ArtifactType.AI_DOCUMENT_HEATMAP,
            ArtifactType.AI_DOCUMENT_MASK,
            ArtifactType.AI_DOCUMENT_OVERLAY,
            ArtifactType.AI_DOCUMENT_PREDICTION,
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
