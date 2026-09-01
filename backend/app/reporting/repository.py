"""Repository operations for forensic reports."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.forensic_report import ForensicReport
from backend.app.reporting.models import ReportStatus


class ReportRepository:
    """Encapsulate forensic report persistence queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_report(self, report_id: UUID) -> ForensicReport | None:
        return await self.session.get(ForensicReport, report_id)

    async def get_active_for_case(self, case_id: UUID) -> ForensicReport | None:
        result = await self.session.scalars(
            select(ForensicReport).where(
                ForensicReport.case_id == case_id,
                ForensicReport.status.in_(
                    [ReportStatus.QUEUED, ReportStatus.GENERATING]
                ),
            )
        )
        return result.first()

    async def get_latest_for_case(self, case_id: UUID) -> ForensicReport | None:
        result = await self.session.scalars(
            select(ForensicReport)
            .where(ForensicReport.case_id == case_id)
            .order_by(ForensicReport.created_at.desc())
            .limit(1)
        )
        return result.first()

    async def list_reports_for_case(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[ForensicReport], int]:
        filters = [ForensicReport.case_id == case_id]
        total = await self.session.scalar(
            select(func.count()).select_from(ForensicReport).where(*filters)
        )
        result = await self.session.scalars(
            select(ForensicReport)
            .where(*filters)
            .order_by(ForensicReport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def add_report(self, report: ForensicReport) -> ForensicReport:
        self.session.add(report)
        await self.session.flush()
        return report
