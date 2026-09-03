"""Version-one system administration endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_system_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.system.schemas import (
    DiagnosticsResponse,
    DiagnosticsRunResponse,
    HealthSnapshotResponse,
    JobsSummaryResponse,
    MetricsResponse,
    StorageStatsResponse,
)
from backend.app.system.service import SystemService

router = APIRouter(prefix="/system", tags=["system-admin"])
SystemServiceDependency = Annotated[
    SystemService, Depends(get_system_service),
]


@router.get(
    "/health",
    response_model=ApiResponse[HealthSnapshotResponse],
    summary="Get system health snapshot",
)
async def get_system_health(
    service: SystemServiceDependency,
) -> ApiResponse[HealthSnapshotResponse]:
    """Return service, database, redis, and resource health."""
    return ApiResponse(
        data=await service.get_health(),
        request_id=get_request_id(),
    )


@router.get(
    "/metrics",
    response_model=ApiResponse[MetricsResponse],
    summary="Get operational metrics",
)
async def get_system_metrics(
    service: SystemServiceDependency,
) -> ApiResponse[MetricsResponse]:
    """Return deterministic operational metrics."""
    return ApiResponse(
        data=await service.get_metrics(),
        request_id=get_request_id(),
    )


@router.get(
    "/jobs",
    response_model=ApiResponse[JobsSummaryResponse],
    summary="Get background job summary",
)
async def get_system_jobs(
    service: SystemServiceDependency,
) -> ApiResponse[JobsSummaryResponse]:
    """Return job counts across pipeline categories."""
    return ApiResponse(
        data=await service.get_jobs(),
        request_id=get_request_id(),
    )


@router.get(
    "/storage",
    response_model=ApiResponse[StorageStatsResponse],
    summary="Get storage utilization",
)
async def get_system_storage(
    service: SystemServiceDependency,
) -> ApiResponse[StorageStatsResponse]:
    """Return storage usage statistics."""
    return ApiResponse(
        data=await service.get_storage(),
        request_id=get_request_id(),
    )


@router.get(
    "/diagnostics",
    response_model=ApiResponse[DiagnosticsResponse],
    summary="Get latest diagnostics results",
)
async def get_system_diagnostics(
    service: SystemServiceDependency,
) -> ApiResponse[DiagnosticsResponse]:
    """Return current diagnostics without persisting."""
    return ApiResponse(
        data=await service.get_diagnostics(),
        request_id=get_request_id(),
    )


@router.post(
    "/diagnostics/run",
    response_model=ApiResponse[DiagnosticsRunResponse],
    summary="Run system diagnostics",
)
async def run_system_diagnostics(
    service: SystemServiceDependency,
) -> ApiResponse[DiagnosticsRunResponse]:
    """Execute diagnostics and persist results."""
    return ApiResponse(
        data=await service.run_diagnostics(),
        request_id=get_request_id(),
    )
