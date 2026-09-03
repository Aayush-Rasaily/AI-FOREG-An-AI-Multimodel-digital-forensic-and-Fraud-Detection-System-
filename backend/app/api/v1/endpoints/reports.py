"""Version-one forensic report endpoints."""

from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import Response, StreamingResponse

from backend.app.api.dependencies import get_report_service, get_storage_service
from backend.app.application.services.storage import StorageService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.reporting.schemas import (
    ForensicReportDetailResponse,
    ForensicReportListResponse,
    ForensicReportResponse,
    ForensicReportStatusResponse,
)
from backend.app.reporting.service import ReportService

router = APIRouter(tags=["reports"])
ReportServiceDependency = Annotated[ReportService, Depends(get_report_service)]
StorageServiceDependency = Annotated[StorageService, Depends(get_storage_service)]


@router.post(
    "/cases/{case_id}/reports",
    response_model=ApiResponse[ForensicReportResponse],
    status_code=202,
    summary="Queue forensic investigation report generation",
)
async def generate_case_report(
    case_id: UUID,
    background_tasks: BackgroundTasks,
    service: ReportServiceDependency,
) -> ApiResponse[ForensicReportResponse]:
    """Queue a stable forensic report snapshot for one case."""

    report = await service.create_report(case_id)
    background_tasks.add_task(service.run, report.id)
    return ApiResponse(data=report, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/reports",
    response_model=ApiResponse[ForensicReportListResponse],
    summary="List forensic reports for a case",
)
async def list_case_reports(
    case_id: UUID,
    service: ReportServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ForensicReportListResponse]:
    """Return forensic report history for one case."""

    return ApiResponse(
        data=await service.list_reports(case_id, limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/reports/latest",
    response_model=ApiResponse[ForensicReportDetailResponse],
    summary="Get latest forensic report for a case",
)
async def get_latest_case_report(
    case_id: UUID,
    service: ReportServiceDependency,
) -> ApiResponse[ForensicReportDetailResponse]:
    """Return the latest generated forensic report."""

    return ApiResponse(
        data=await service.get_latest(case_id),
        request_id=get_request_id(),
    )


@router.get(
    "/reports/{report_id}",
    response_model=ApiResponse[ForensicReportDetailResponse],
    summary="Get one forensic report",
)
async def get_forensic_report(
    report_id: UUID,
    service: ReportServiceDependency,
) -> ApiResponse[ForensicReportDetailResponse]:
    """Return one forensic report snapshot."""

    return ApiResponse(
        data=await service.get_report(report_id),
        request_id=get_request_id(),
    )


@router.get(
    "/reports/{report_id}/status",
    response_model=ApiResponse[ForensicReportStatusResponse],
    summary="Get forensic report generation status",
)
async def get_forensic_report_status(
    report_id: UUID,
    service: ReportServiceDependency,
) -> ApiResponse[ForensicReportStatusResponse]:
    """Return report generation status."""

    return ApiResponse(
        data=await service.get_status(report_id),
        request_id=get_request_id(),
    )


@router.get(
    "/reports/{report_id}/download",
    summary="Download forensic report",
)
async def download_forensic_report(
    report_id: UUID,
    service: ReportServiceDependency,
    storage: StorageServiceDependency,
    fmt: Annotated[
        str | None, Query(alias="format")
    ] = None,
) -> Response:
    """Download a report in JSON, Markdown, HTML, or PDF."""

    if fmt in ("json", "md", "html"):
        from backend.app.reporting.renderer import render_report

        content = await service.get_report_content(report_id)
        payload, media_type, suffix = render_report(content, fmt)  # type: ignore[arg-type]
        return Response(
            content=payload,
            media_type=media_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{suffix}"'
                ),
            },
        )

    storage_key, filename = await service.get_pdf_storage_key(
        report_id,
    )

    async def stream() -> AsyncIterator[bytes]:
        async with storage.open(storage_key) as handle:
            while chunk := handle.read(1024 * 1024):
                yield chunk

    return StreamingResponse(
        stream(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
        },
    )
