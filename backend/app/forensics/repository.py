"""Repository operations for forensic analysis runs and findings."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.domain.processing import ArtifactType
from backend.app.models.forensics import AnalysisRun, Finding, FindingRegion
from backend.app.models.processing import Artifact


class ForensicRepository:
    """Encapsulate bounded forensic persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(self, analysis_run_id: UUID) -> AnalysisRun | None:
        """Return one analysis run."""

        return await self.session.get(AnalysisRun, analysis_run_id)

    async def get_run_with_findings(self, analysis_run_id: UUID) -> AnalysisRun | None:
        """Return one analysis run with findings and regions loaded."""

        result = await self.session.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.id == analysis_run_id)
            .options(
                selectinload(AnalysisRun.findings).selectinload(Finding.regions),
            )
        )
        return result.first()

    async def list_runs_for_evidence(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[AnalysisRun], int]:
        """Return analysis history for one evidence item."""

        filters = [AnalysisRun.evidence_id == evidence_id]
        total = await self.session.scalar(
            select(func.count()).select_from(AnalysisRun).where(*filters)
        )
        result = await self.session.scalars(
            select(AnalysisRun)
            .where(*filters)
            .order_by(AnalysisRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def latest_run_for_evidence(self, evidence_id: UUID) -> AnalysisRun | None:
        """Return the most recent analysis run."""

        result = await self.session.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.evidence_id == evidence_id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(1)
        )
        return result.first()

    async def add_run(self, run: AnalysisRun) -> AnalysisRun:
        """Stage and flush an analysis run."""

        self.session.add(run)
        await self.session.flush()
        return run

    async def add_finding(self, finding: Finding) -> Finding:
        """Stage and flush a finding."""

        self.session.add(finding)
        await self.session.flush()
        return finding

    async def add_region(self, region: FindingRegion) -> FindingRegion:
        """Stage and flush a finding region."""

        self.session.add(region)
        await self.session.flush()
        return region

    async def list_findings_for_evidence(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Finding], int]:
        """Return findings for one evidence item across all runs."""

        filters = [Finding.evidence_id == evidence_id]
        total = await self.session.scalar(
            select(func.count()).select_from(Finding).where(*filters)
        )
        result = await self.session.scalars(
            select(Finding)
            .where(*filters)
            .options(selectinload(Finding.regions))
            .order_by(Finding.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def list_heatmap_artifacts(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Artifact], int]:
        """Return forensic heatmap and ELA artifacts for one evidence item."""

        artifact_types = (
            ArtifactType.ELA_RESULT,
            ArtifactType.FORENSIC_HEATMAP,
            ArtifactType.FORENSIC_MASK,
            ArtifactType.FORENSIC_OVERLAY,
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
