"""Repository operations for reference comparison runs and differences."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.domain.processing import ArtifactType
from backend.app.models.comparison import (
    ComparisonRun,
    Difference,
    DifferenceRegion,
    ReferenceEvidence,
)
from backend.app.models.processing import Artifact


class ComparisonRepository:
    """Encapsulate bounded comparison persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_reference(self, reference_id: UUID) -> ReferenceEvidence | None:
        """Return one reference evidence record."""

        return await self.session.get(ReferenceEvidence, reference_id)

    async def list_references_for_case(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[ReferenceEvidence], int]:
        """Return trusted references registered for one case."""

        filters = [ReferenceEvidence.case_id == case_id]
        total = await self.session.scalar(
            select(func.count()).select_from(ReferenceEvidence).where(*filters)
        )
        result = await self.session.scalars(
            select(ReferenceEvidence)
            .where(*filters)
            .order_by(ReferenceEvidence.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def add_reference(self, reference: ReferenceEvidence) -> ReferenceEvidence:
        """Stage and flush a reference evidence record."""

        self.session.add(reference)
        await self.session.flush()
        return reference

    async def get_run(self, comparison_run_id: UUID) -> ComparisonRun | None:
        """Return one comparison run."""

        return await self.session.get(ComparisonRun, comparison_run_id)

    async def get_run_with_differences(
        self,
        comparison_run_id: UUID,
    ) -> ComparisonRun | None:
        """Return one comparison run with differences and regions loaded."""

        result = await self.session.scalars(
            select(ComparisonRun)
            .where(ComparisonRun.id == comparison_run_id)
            .options(
                selectinload(ComparisonRun.differences).selectinload(
                    Difference.regions
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
    ) -> tuple[list[ComparisonRun], int]:
        """Return comparison history for one evidence item."""

        filters = [ComparisonRun.evidence_id == evidence_id]
        total = await self.session.scalar(
            select(func.count()).select_from(ComparisonRun).where(*filters)
        )
        result = await self.session.scalars(
            select(ComparisonRun)
            .where(*filters)
            .order_by(ComparisonRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def latest_run_for_evidence(
        self,
        evidence_id: UUID,
    ) -> ComparisonRun | None:
        """Return the most recent comparison run."""

        result = await self.session.scalars(
            select(ComparisonRun)
            .where(ComparisonRun.evidence_id == evidence_id)
            .order_by(ComparisonRun.created_at.desc())
            .limit(1)
        )
        return result.first()

    async def add_run(self, run: ComparisonRun) -> ComparisonRun:
        """Stage and flush a comparison run."""

        self.session.add(run)
        await self.session.flush()
        return run

    async def add_difference(self, difference: Difference) -> Difference:
        """Stage and flush a difference."""

        self.session.add(difference)
        await self.session.flush()
        return difference

    async def add_region(self, region: DifferenceRegion) -> DifferenceRegion:
        """Stage and flush a difference region."""

        self.session.add(region)
        await self.session.flush()
        return region

    async def list_differences_for_evidence(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Difference], int]:
        """Return differences for one evidence item across all runs."""

        filters = [Difference.evidence_id == evidence_id]
        total = await self.session.scalar(
            select(func.count()).select_from(Difference).where(*filters)
        )
        result = await self.session.scalars(
            select(Difference)
            .where(*filters)
            .options(selectinload(Difference.regions))
            .order_by(Difference.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def list_comparison_artifacts(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Artifact], int]:
        """Return comparison visualization artifacts for one evidence item."""

        artifact_types = (
            ArtifactType.COMPARISON_MASK,
            ArtifactType.COMPARISON_OVERLAY,
            ArtifactType.COMPARISON_SIDE_BY_SIDE,
            ArtifactType.COMPARISON_OUTPUT,
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
