"""Version-one operational monitoring endpoints (Phase 8D)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_monitoring_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.monitoring.schemas import (
    MonitoringDashboardResponse,
    MonitoringRefreshResponse,
    MonitoringSectionResponse,
    SystemHealthResponse,
)
from backend.app.monitoring.service import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
MonitoringServiceDependency = Annotated[
    MonitoringService,
    Depends(get_monitoring_service),
]


@router.get(
    "/dashboard",
    response_model=ApiResponse[MonitoringDashboardResponse],
    summary="Operational monitoring dashboard",
)
async def get_monitoring_dashboard(
    service: MonitoringServiceDependency,
) -> ApiResponse[MonitoringDashboardResponse]:
    return ApiResponse(
        data=await service.get_dashboard(),
        request_id=get_request_id(),
    )


@router.get(
    "/system-health",
    response_model=ApiResponse[SystemHealthResponse],
    summary="Platform health assessment",
)
async def get_system_health(
    service: MonitoringServiceDependency,
) -> ApiResponse[SystemHealthResponse]:
    return ApiResponse(
        data=await service.get_system_health(),
        request_id=get_request_id(),
    )


@router.get(
    "/processing",
    response_model=ApiResponse[MonitoringSectionResponse],
    summary="Processing operational metrics",
)
async def get_processing_metrics(
    service: MonitoringServiceDependency,
) -> ApiResponse[MonitoringSectionResponse]:
    return ApiResponse(
        data=await service.get_processing(),
        request_id=get_request_id(),
    )


@router.get(
    "/ai",
    response_model=ApiResponse[MonitoringSectionResponse],
    summary="AI operational metrics",
)
async def get_ai_metrics(
    service: MonitoringServiceDependency,
) -> ApiResponse[MonitoringSectionResponse]:
    return ApiResponse(
        data=await service.get_ai(),
        request_id=get_request_id(),
    )


@router.get(
    "/api",
    response_model=ApiResponse[MonitoringSectionResponse],
    summary="API usage metrics derived from audit events",
)
async def get_api_metrics(
    service: MonitoringServiceDependency,
) -> ApiResponse[MonitoringSectionResponse]:
    return ApiResponse(
        data=await service.get_api(),
        request_id=get_request_id(),
    )


@router.get(
    "/activity",
    response_model=ApiResponse[MonitoringSectionResponse],
    summary="User and investigation activity metrics",
)
async def get_activity_metrics(
    service: MonitoringServiceDependency,
) -> ApiResponse[MonitoringSectionResponse]:
    return ApiResponse(
        data=await service.get_activity(),
        request_id=get_request_id(),
    )


@router.get(
    "/bottlenecks",
    response_model=ApiResponse[MonitoringSectionResponse],
    summary="Processing and detector bottlenecks",
)
async def get_bottlenecks(
    service: MonitoringServiceDependency,
) -> ApiResponse[MonitoringSectionResponse]:
    return ApiResponse(
        data=await service.get_bottlenecks(),
        request_id=get_request_id(),
    )


@router.get(
    "/audit-summary",
    response_model=ApiResponse[MonitoringSectionResponse],
    summary="Audit analytics summary",
)
async def get_audit_summary(
    service: MonitoringServiceDependency,
) -> ApiResponse[MonitoringSectionResponse]:
    return ApiResponse(
        data=await service.get_audit_summary(),
        request_id=get_request_id(),
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[MonitoringRefreshResponse],
    status_code=201,
    summary="Recompute and persist monitoring snapshots",
)
async def refresh_monitoring(
    service: MonitoringServiceDependency,
) -> ApiResponse[MonitoringRefreshResponse]:
    return ApiResponse(
        data=await service.refresh(),
        request_id=get_request_id(),
    )
