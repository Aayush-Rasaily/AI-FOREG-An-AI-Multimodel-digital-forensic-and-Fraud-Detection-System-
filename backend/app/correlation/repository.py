"""Repository operations for cross-evidence correlation."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.correlation.models import CorrelationRunStatus
from backend.app.models.correlation import (
    CorrelationAnalysisRun,
    CorrelationSupportRecord,
    EvidenceCorrelationRecord,
)


class CorrelationRepository:
    """Encapsulate correlation persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(self, run_id: UUID) -> CorrelationAnalysisRun | None:
        return await self.session.get(CorrelationAnalysisRun, run_id)

    async def get_run_with_details(
        self,
        run_id: UUID,
    ) -> CorrelationAnalysisRun | None:
        result = await self.session.scalars(
            select(CorrelationAnalysisRun)
            .where(CorrelationAnalysisRun.id == run_id)
            .options(
                selectinload(CorrelationAnalysisRun.correlations).selectinload(
                    EvidenceCorrelationRecord.support_records
                )
            )
        )
        return result.first()

    async def get_active_for_case(self, case_id: UUID) -> CorrelationAnalysisRun | None:
        result = await self.session.scalars(
            select(CorrelationAnalysisRun).where(
                CorrelationAnalysisRun.case_id == case_id,
                CorrelationAnalysisRun.status.in_(
                    [CorrelationRunStatus.QUEUED, CorrelationRunStatus.RUNNING]
                ),
            )
        )
        return result.first()

    async def get_latest_for_case(self, case_id: UUID) -> CorrelationAnalysisRun | None:
        result = await self.session.scalars(
            select(CorrelationAnalysisRun)
            .where(CorrelationAnalysisRun.case_id == case_id)
            .order_by(CorrelationAnalysisRun.created_at.desc())
            .limit(1)
            .options(
                selectinload(CorrelationAnalysisRun.correlations).selectinload(
                    EvidenceCorrelationRecord.support_records
                )
            )
        )
        return result.first()

    async def list_for_case(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[CorrelationAnalysisRun], int]:
        filters = [CorrelationAnalysisRun.case_id == case_id]
        total = await self.session.scalar(
            select(func.count()).select_from(CorrelationAnalysisRun).where(*filters)
        )
        result = await self.session.scalars(
            select(CorrelationAnalysisRun)
            .where(*filters)
            .order_by(CorrelationAnalysisRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def get_correlation(
        self,
        correlation_id: UUID,
    ) -> EvidenceCorrelationRecord | None:
        result = await self.session.scalars(
            select(EvidenceCorrelationRecord)
            .where(EvidenceCorrelationRecord.id == correlation_id)
            .options(selectinload(EvidenceCorrelationRecord.support_records))
        )
        return result.first()

    async def list_for_evidence(
        self,
        evidence_id: UUID,
    ) -> list[EvidenceCorrelationRecord]:
        result = await self.session.scalars(
            select(EvidenceCorrelationRecord)
            .where(
                or_(
                    EvidenceCorrelationRecord.left_evidence_id == evidence_id,
                    EvidenceCorrelationRecord.right_evidence_id == evidence_id,
                )
            )
            .order_by(EvidenceCorrelationRecord.score.desc())
            .options(selectinload(EvidenceCorrelationRecord.support_records))
        )
        return list(result)

    async def list_by_type(
        self,
        case_id: UUID,
        correlation_type: str,
    ) -> list[EvidenceCorrelationRecord]:
        latest = await self.get_latest_for_case(case_id)
        if latest is None:
            return []
        return [
            item
            for item in latest.correlations
            if item.correlation_type.value == correlation_type
        ]

    async def add_run(self, run: CorrelationAnalysisRun) -> CorrelationAnalysisRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_correlation(
        self,
        record: EvidenceCorrelationRecord,
    ) -> EvidenceCorrelationRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def add_support(
        self,
        record: CorrelationSupportRecord,
    ) -> CorrelationSupportRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def delete_run(self, run_id: UUID) -> None:
        run = await self.get_run(run_id)
        if run is not None:
            await self.session.delete(run)
            await self.session.flush()
