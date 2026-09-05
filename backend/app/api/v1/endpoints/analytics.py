"""Phase 9G investigation analytics endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.analytics.schemas import (
    AnalyticsExportResponse,
    AnalyticsRunResponse,
    AnalyticsSectionResponse,
)
from backend.app.analytics.service import AnalyticsService
from backend.app.api.dependencies import get_analytics_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["analytics"])
ServiceDependency = Annotated[
    AnalyticsService,
    Depends(get_analytics_service),
]


@router.post(
    "/analytics/refresh",
    response_model=ApiResponse[AnalyticsRunResponse],
)
async def refresh_analytics(
    service: ServiceDependency,
) -> ApiResponse[AnalyticsRunResponse]:
    data = await service.refresh()
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/analytics",
    response_model=ApiResponse[AnalyticsRunResponse],
)
async def get_analytics(
    service: ServiceDependency,
) -> ApiResponse[AnalyticsRunResponse]:
    data = await service.get_latest()
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/analytics/dashboard",
    response_model=ApiResponse[dict],
)
async def get_analytics_dashboard(
    service: ServiceDependency,
) -> ApiResponse[dict]:
    data = await service.get_dashboard()
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/analytics/cases",
    response_model=ApiResponse[AnalyticsSectionResponse],
)
async def get_analytics_cases(
    service: ServiceDependency,
) -> ApiResponse[AnalyticsSectionResponse]:
    data = await service.get_section("cases")
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/analytics/evidence",
    response_model=ApiResponse[AnalyticsSectionResponse],
)
async def get_analytics_evidence(
    service: ServiceDependency,
) -> ApiResponse[AnalyticsSectionResponse]:
    data = await service.get_section("evidence")
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/analytics/ai",
    response_model=ApiResponse[AnalyticsSectionResponse],
)
async def get_analytics_ai(
    service: ServiceDependency,
) -> ApiResponse[AnalyticsSectionResponse]:
    data = await service.get_section("ai")
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/analytics/workflow",
    response_model=ApiResponse[AnalyticsSectionResponse],
)
async def get_analytics_workflow(
    service: ServiceDependency,
) -> ApiResponse[AnalyticsSectionResponse]:
    data = await service.get_section("workflow")
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/analytics/integrity",
    response_model=ApiResponse[AnalyticsSectionResponse],
)
async def get_analytics_integrity(
    service: ServiceDependency,
) -> ApiResponse[AnalyticsSectionResponse]:
    data = await service.get_section("integrity")
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/analytics/export",
    response_model=ApiResponse[AnalyticsExportResponse],
)
async def export_analytics(
    service: ServiceDependency,
) -> ApiResponse[AnalyticsExportResponse]:
    data = await service.export()
    return ApiResponse(data=data, request_id=get_request_id())
