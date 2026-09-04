"""Persistence helpers for security governance entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit import AuditEvent
from backend.app.models.case import Case
from backend.app.models.collaboration import CaseWorkflowState
from backend.app.models.correlation import CorrelationAnalysisRun
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.evidence import Evidence
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.fusion import FusionAnalysisRun
from backend.app.models.security import (
    CaseAccessRecord,
    ComplianceReport,
    PolicyViolation,
    SecurityPermission,
    SecurityRole,
)
from backend.app.models.timeline import InvestigationTimeline
from backend.app.models.user import User
from backend.app.models.workflow import InvestigationWorkflow, WorkflowReview


class SecurityRepository:
    """Data-access layer for Phase 8F security tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: object) -> None:
        self.session.add(row)

    async def get_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def get_user(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def list_roles(self) -> list[SecurityRole]:
        result = await self.session.execute(
            select(SecurityRole).order_by(SecurityRole.code.asc())
        )
        return list(result.scalars().all())

    async def list_permissions(self) -> list[SecurityPermission]:
        result = await self.session.execute(
            select(SecurityPermission).order_by(
                SecurityPermission.code.asc(),
            )
        )
        return list(result.scalars().all())

    async def count_roles(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(SecurityRole)
        )
        return int(result.scalar_one())

    async def list_case_access(self, case_id: UUID) -> list[CaseAccessRecord]:
        result = await self.session.execute(
            select(CaseAccessRecord)
            .where(CaseAccessRecord.case_id == case_id)
            .order_by(
                CaseAccessRecord.granted_at.asc(),
                CaseAccessRecord.id.asc(),
            )
        )
        return list(result.scalars().all())

    async def get_active_access(
        self,
        case_id: UUID,
        user_id: UUID,
    ) -> CaseAccessRecord | None:
        result = await self.session.execute(
            select(CaseAccessRecord).where(
                CaseAccessRecord.case_id == case_id,
                CaseAccessRecord.user_id == user_id,
                CaseAccessRecord.active.is_(True),
            )
        )
        return result.scalars().first()

    async def get_access_record(
        self,
        case_id: UUID,
        record_id: UUID,
    ) -> CaseAccessRecord | None:
        result = await self.session.execute(
            select(CaseAccessRecord).where(
                CaseAccessRecord.case_id == case_id,
                CaseAccessRecord.id == record_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_violations(
        self,
        *,
        case_id: UUID | None = None,
        open_only: bool = False,
    ) -> list[PolicyViolation]:
        stmt = select(PolicyViolation)
        if case_id is not None:
            stmt = stmt.where(PolicyViolation.case_id == case_id)
        if open_only:
            stmt = stmt.where(PolicyViolation.resolved_at.is_(None))
        stmt = stmt.order_by(
            PolicyViolation.detected_at.asc(),
            PolicyViolation.id.asc(),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_evidence(self, case_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Evidence)
            .where(Evidence.case_id == case_id)
        )
        return int(result.scalar_one())

    async def count_evidence_with_hash(self, case_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Evidence)
            .where(
                Evidence.case_id == case_id,
                Evidence.sha256_hash.is_not(None),
            )
        )
        return int(result.scalar_one())

    async def count_custody_events(self, case_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ChainOfCustodyEvent)
            .join(Evidence, ChainOfCustodyEvent.evidence_id == Evidence.id)
            .where(Evidence.case_id == case_id)
        )
        return int(result.scalar_one())

    async def count_audit_events(self, case_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.case_id == case_id)
        )
        return int(result.scalar_one())

    async def get_investigation_workflow(
        self, case_id: UUID,
    ) -> InvestigationWorkflow | None:
        result = await self.session.execute(
            select(InvestigationWorkflow).where(
                InvestigationWorkflow.case_id == case_id
            )
        )
        return result.scalar_one_or_none()

    async def get_collab_workflow(
        self, case_id: UUID,
    ) -> CaseWorkflowState | None:
        result = await self.session.execute(
            select(CaseWorkflowState).where(
                CaseWorkflowState.case_id == case_id
            )
        )
        return result.scalar_one_or_none()

    async def count_reports(self, case_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ForensicReport)
            .where(ForensicReport.case_id == case_id)
        )
        return int(result.scalar_one())

    async def count_reports_with_provenance(self, case_id: UUID) -> int:
        rows = await self.session.execute(
            select(ForensicReport).where(ForensicReport.case_id == case_id)
        )
        count = 0
        for report in rows.scalars().all():
            provenance = getattr(report, "provenance_json", None) or {}
            if provenance:
                count += 1
        return count

    async def count_approved_report_reviews(self, case_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(WorkflowReview)
            .where(
                WorkflowReview.case_id == case_id,
                WorkflowReview.review_kind == "report",
                WorkflowReview.status.in_(("approved", "published")),
            )
        )
        return int(result.scalar_one())

    async def count_published_without_approval(self, case_id: UUID) -> int:
        result = await self.session.execute(
            select(WorkflowReview).where(
                WorkflowReview.case_id == case_id,
                WorkflowReview.review_kind == "report",
                WorkflowReview.status == "published",
            )
        )
        count = 0
        for review in result.scalars().all():
            history = list(review.history_json or [])
            statuses = [str(item.get("status")) for item in history]
            if "approved" not in statuses:
                count += 1
        return count

    async def count_fusion(self, case_id: UUID) -> tuple[int, int]:
        evidence_ids = (
            await self.session.execute(
                select(Evidence.id).where(Evidence.case_id == case_id)
            )
        ).scalars().all()
        if not evidence_ids:
            return 0, 0
        rows = await self.session.execute(
            select(FusionAnalysisRun).where(
                FusionAnalysisRun.evidence_id.in_(list(evidence_ids))
            )
        )
        total = 0
        with_prov = 0
        for run in rows.scalars().all():
            total += 1
            provenance = getattr(run, "provenance_json", None) or {}
            if provenance:
                with_prov += 1
        return total, with_prov

    async def count_correlation(self, case_id: UUID) -> tuple[int, int]:
        rows = await self.session.execute(
            select(CorrelationAnalysisRun).where(
                CorrelationAnalysisRun.case_id == case_id
            )
        )
        total = 0
        with_prov = 0
        for run in rows.scalars().all():
            total += 1
            provenance = getattr(run, "provenance_json", None) or {}
            if provenance:
                with_prov += 1
        return total, with_prov

    async def has_timeline(self, case_id: UUID) -> bool:
        result = await self.session.execute(
            select(InvestigationTimeline.id)
            .where(InvestigationTimeline.case_id == case_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def list_compliance_reports(
        self, case_id: UUID | None = None,
    ) -> list[ComplianceReport]:
        stmt = select(ComplianceReport)
        if case_id is not None:
            stmt = stmt.where(ComplianceReport.case_id == case_id)
        stmt = stmt.order_by(
            ComplianceReport.generated_at.asc(),
            ComplianceReport.id.asc(),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
