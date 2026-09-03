"""Application service for forensic investigation reports."""

from __future__ import annotations

import hashlib
import io
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.core.config import Settings
from backend.app.core.exceptions import ConflictError, ResourceNotFoundError
from backend.app.models.case import Case
from backend.app.models.forensic_report import ForensicReport
from backend.app.reporting.engine import ReportEngine
from backend.app.reporting.exceptions import ReportingError
from backend.app.reporting.models import ReportStatus
from backend.app.reporting.pdf import build_report_pdf
from backend.app.reporting.policy import ENGINE_VERSION, REPORT_VERSION
from backend.app.reporting.repository import ReportRepository
from backend.app.reporting.schemas import (
    ForensicReportDetailResponse,
    ForensicReportListResponse,
    ForensicReportResponse,
    ForensicReportStatusResponse,
)

logger = logging.getLogger(__name__)


def _report_storage_key(case_id: UUID, report_id: UUID) -> str:
    return f"reports/{case_id}/{report_id}.pdf"


class ReportService:
    """Queue and execute forensic investigation report generation."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: ReportEngine | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.engine = engine or ReportEngine()
        self.repository = ReportRepository(session)

    async def create_report(self, case_id: UUID) -> ForensicReportResponse:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise ResourceNotFoundError("The requested case was not found.")
        active = await self.repository.get_active_for_case(case_id)
        if active is not None:
            raise ConflictError("An active report generation job already exists.")
        report = ForensicReport(
            id=uuid4(),
            case_id=case_id,
            status=ReportStatus.QUEUED,
            report_version=REPORT_VERSION,
            engine_version=ENGINE_VERSION,
            evidence_hashes_json=[],
            content_json={},
            metadata_json={"case_number": case.case_number},
            provenance_json={"case_id": str(case_id), "case_number": case.case_number},
        )
        try:
            await self.repository.add_report(report)
            await self.session.commit()
            await self.session.refresh(report)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "An active report generation job already exists.",
            ) from exc
        return self._report_response(report)

    async def run(self, report_id: UUID) -> None:
        report = await self.repository.get_report(report_id)
        if report is None or report.status != ReportStatus.QUEUED:
            return
        case = await self.session.get(Case, report.case_id)
        if case is None:
            await self._fail_report(
                report_id,
                "CASE_NOT_FOUND",
                "The case record is no longer available.",
            )
            return
        report.status = ReportStatus.GENERATING
        report.started_at = datetime.now(UTC)
        try:
            await self.session.commit()
            result = await self.engine.generate(
                self.session,
                case=case,
                report_id=report_id,
            )
            if result.status != ReportStatus.COMPLETED:
                raise ReportingError(
                    result.error_code or "REPORT_GENERATION_FAILED",
                    result.error_message_safe or "Report generation failed.",
                )
            pdf_bytes = build_report_pdf(result.content)
            pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
            storage_key = _report_storage_key(case.id, report_id)
            await self.storage.save_stream(
                io.BytesIO(pdf_bytes),
                storage_key,
                max_bytes=self.settings.max_upload_size_mb * 1024 * 1024,
                chunk_size=self.settings.upload_chunk_size_bytes,
            )
            intelligence_run_id = result.provenance.get(
                "case_intelligence_run_id",
            )
            report.status = ReportStatus.COMPLETED
            report.content_json = result.content
            report.evidence_hashes_json = list(
                result.provenance.get("evidence_hashes", [])
            )
            report.report_checksum = result.content.get(
                "report_checksum",
            )
            report.included_analysis_run_ids_json = (
                result.metadata.get("included_analysis_run_ids")
            )
            report.pdf_storage_key = storage_key
            report.pdf_sha256 = pdf_sha256
            report.provenance_json = {
                **result.provenance,
                "report_sha256": pdf_sha256,
            }
            report.metadata_json = {
                **report.metadata_json,
                **result.metadata,
            }
            report.fusion_policy_version = (
                result.content.get("sections", {})
                .get("technical_appendix", {})
                .get("fusion_policy_versions", [None])[0]
                if result.content.get("sections", {})
                .get("technical_appendix", {})
                .get("fusion_policy_versions")
                else None
            )
            report.case_intelligence_policy_version = (
                result.content.get("sections", {})
                .get("technical_appendix", {})
                .get("case_intelligence_policy_version")
            )
            if intelligence_run_id:
                report.case_intelligence_run_id = UUID(str(intelligence_run_id))
            report.completed_at = datetime.now(UTC)
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            if isinstance(exc, ReportingError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "REPORT_GENERATION_FAILED"
                safe_message = "The forensic report generation pipeline failed."
            await self._fail_report(report_id, error_code, safe_message)
            logger.exception(
                "Forensic report generation failed",
                extra={"report_id": str(report_id), "case_id": str(report.case_id)},
            )

    async def list_reports(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> ForensicReportListResponse:
        if await self.session.get(Case, case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        reports, total = await self.repository.list_reports_for_case(
            case_id,
            limit=limit,
            offset=offset,
        )
        return ForensicReportListResponse(
            items=[self._report_response(item) for item in reports],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_latest(self, case_id: UUID) -> ForensicReportDetailResponse:
        if await self.session.get(Case, case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        report = await self.repository.get_latest_for_case(case_id)
        if report is None:
            raise ResourceNotFoundError("No forensic report exists for this case.")
        return self._detail_response(report)

    async def get_report(self, report_id: UUID) -> ForensicReportDetailResponse:
        report = await self.repository.get_report(report_id)
        if report is None:
            raise ResourceNotFoundError("The requested forensic report was not found.")
        return self._detail_response(report)

    async def get_status(self, report_id: UUID) -> ForensicReportStatusResponse:
        report = await self.repository.get_report(report_id)
        if report is None:
            raise ResourceNotFoundError("The requested forensic report was not found.")
        return ForensicReportStatusResponse(
            id=report.id,
            status=report.status,
            error_code=report.error_code,
            error_message=report.error_message,
            completed_at=report.completed_at,
        )

    async def get_pdf_storage_key(self, report_id: UUID) -> tuple[str, str]:
        report = await self.repository.get_report(report_id)
        if report is None:
            raise ResourceNotFoundError(
                "The requested forensic report was not found.",
            )
        if (
            report.status != ReportStatus.COMPLETED
            or not report.pdf_storage_key
        ):
            raise ResourceNotFoundError(
                "The report PDF is not available.",
            )
        filename = f"forensic-report-{report.id}.pdf"
        return report.pdf_storage_key, filename

    async def get_report_content(
        self,
        report_id: UUID,
    ) -> dict[str, Any]:
        """Return the completed report content dict."""
        report = await self.repository.get_report(report_id)
        if report is None:
            raise ResourceNotFoundError(
                "The requested forensic report was not found.",
            )
        if report.status != ReportStatus.COMPLETED:
            raise ResourceNotFoundError(
                "The report is not yet completed.",
            )
        return dict(report.content_json or {})

    async def _fail_report(
        self,
        report_id: UUID,
        error_code: str,
        message: str,
    ) -> None:
        report = await self.repository.get_report(report_id)
        if report is not None:
            report.status = ReportStatus.FAILED
            report.error_code = error_code
            report.error_message = message
            report.completed_at = datetime.now(UTC)
        await self.session.commit()

    @staticmethod
    def _report_response(
        report: ForensicReport,
    ) -> ForensicReportResponse:
        return ForensicReportResponse(
            id=report.id,
            case_id=report.case_id,
            status=report.status,
            report_version=report.report_version,
            engine_version=report.engine_version,
            fusion_policy_version=report.fusion_policy_version,
            case_intelligence_policy_version=(
                report.case_intelligence_policy_version
            ),
            case_intelligence_run_id=(
                report.case_intelligence_run_id
            ),
            evidence_count=len(report.evidence_hashes_json),
            evidence_hashes=list(report.evidence_hashes_json),
            pdf_sha256=report.pdf_sha256,
            has_pdf=bool(report.pdf_storage_key),
            report_checksum=report.report_checksum,
            included_analysis_run_ids=(
                report.included_analysis_run_ids_json or {}
            ),
            created_at=report.created_at,
            started_at=report.started_at,
            completed_at=report.completed_at,
            error_code=report.error_code,
            error_message=report.error_message,
            metadata=report.metadata_json,
            provenance=report.provenance_json,
        )

    def _detail_response(
        self,
        report: ForensicReport,
    ) -> ForensicReportDetailResponse:
        base = self._report_response(report)
        content = report.content_json or {}
        sections = content.get("sections", {})
        return ForensicReportDetailResponse(
            **base.model_dump(),
            content=content,
            executive_summary=sections.get(
                "executive_summary", {},
            ),
            explainability=sections.get("explainability", {}),
            section_order=list(
                content.get("section_order", []),
            ),
        )
