"""Phase 9H platform validation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_platform_validation_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.platform_validation.schemas import (
    HealthReportResponse,
    PlatformValidationRunResponse,
    ReadinessResponse,
    ValidationListResponse,
)
from backend.app.platform_validation.service import PlatformValidationService

router = APIRouter(tags=["platform-validation"])
ServiceDependency = Annotated[
    PlatformValidationService,
    Depends(get_platform_validation_service),
]


@router.post(
    "/platform/validate",
    response_model=ApiResponse[PlatformValidationRunResponse],
)
async def run_platform_validation(
    service: ServiceDependency,
) -> ApiResponse[PlatformValidationRunResponse]:
    data = await service.validate()
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/platform/validation",
    response_model=ApiResponse[ValidationListResponse],
)
async def list_platform_validations(
    service: ServiceDependency,
) -> ApiResponse[ValidationListResponse]:
    data = await service.list_runs()
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/platform/validation/latest",
    response_model=ApiResponse[PlatformValidationRunResponse],
)
async def get_latest_platform_validation(
    service: ServiceDependency,
) -> ApiResponse[PlatformValidationRunResponse]:
    data = await service.get_latest()
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/platform/validation/{run_id}",
    response_model=ApiResponse[PlatformValidationRunResponse],
)
async def get_platform_validation_run(
    run_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[PlatformValidationRunResponse]:
    data = await service.get_run(run_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/platform/readiness",
    response_model=ApiResponse[ReadinessResponse],
)
async def get_platform_readiness(
    service: ServiceDependency,
) -> ApiResponse[ReadinessResponse]:
    data = await service.get_readiness()
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/platform/health/report",
    response_model=ApiResponse[HealthReportResponse],
)
async def get_platform_health_report(
    service: ServiceDependency,
) -> ApiResponse[HealthReportResponse]:
    data = await service.get_health_report()
    return ApiResponse(data=data, request_id=get_request_id())
