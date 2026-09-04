"""Phase 8G production readiness and release endpoints.

Additive under `/system/*`. Existing Phase 7F `/system/health|metrics|...`
and Phase 1 `/health|/health/live` probes remain unchanged.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from backend.app.api.dependencies import SessionDependency, get_runtime_settings
from backend.app.core.config import Settings
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.deployment.schemas import (
    ConfigurationResponse,
    LivenessResponse,
    ReadinessResponse,
    ReleaseCheckResponse,
    ReleaseResponse,
    StartupValidationResponse,
    ValidationResponse,
    VersionResponse,
)
from backend.app.deployment.service import DeploymentService

router = APIRouter(prefix="/system", tags=["system-release"])


def get_deployment_service(
    session: SessionDependency,
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> DeploymentService:
    return DeploymentService(session=session, settings=settings)


DeploymentServiceDependency = Annotated[
    DeploymentService, Depends(get_deployment_service),
]


@router.get("/version", response_model=ApiResponse[VersionResponse])
async def get_system_version(
    service: DeploymentServiceDependency,
) -> ApiResponse[VersionResponse]:
    return ApiResponse(data=service.get_version(), request_id=get_request_id())


@router.get("/release", response_model=ApiResponse[ReleaseResponse])
async def get_system_release(
    request: Request,
    service: DeploymentServiceDependency,
) -> ApiResponse[ReleaseResponse]:
    return ApiResponse(
        data=service.get_release(request),
        request_id=get_request_id(),
    )


@router.get("/liveness", response_model=ApiResponse[LivenessResponse])
async def get_system_liveness(
    service: DeploymentServiceDependency,
) -> ApiResponse[LivenessResponse]:
    return ApiResponse(data=service.get_liveness(), request_id=get_request_id())


@router.get("/readiness", response_model=ApiResponse[ReadinessResponse])
async def get_system_readiness(
    request: Request,
    service: DeploymentServiceDependency,
) -> ApiResponse[ReadinessResponse]:
    return ApiResponse(
        data=await service.get_readiness(request),
        request_id=get_request_id(),
    )


@router.get(
    "/startup-validation",
    response_model=ApiResponse[StartupValidationResponse],
)
async def get_startup_validation(
    service: DeploymentServiceDependency,
) -> ApiResponse[StartupValidationResponse]:
    return ApiResponse(
        data=service.get_startup_validation(),
        request_id=get_request_id(),
    )


@router.get("/configuration", response_model=ApiResponse[ConfigurationResponse])
async def get_system_configuration(
    service: DeploymentServiceDependency,
) -> ApiResponse[ConfigurationResponse]:
    return ApiResponse(
        data=service.get_configuration(),
        request_id=get_request_id(),
    )


@router.post("/validate", response_model=ApiResponse[ValidationResponse])
async def post_system_validate(
    request: Request,
    service: DeploymentServiceDependency,
) -> ApiResponse[ValidationResponse]:
    return ApiResponse(
        data=await service.validate(request),
        request_id=get_request_id(),
    )


@router.post("/release-check", response_model=ApiResponse[ReleaseCheckResponse])
async def post_system_release_check(
    request: Request,
    service: DeploymentServiceDependency,
) -> ApiResponse[ReleaseCheckResponse]:
    return ApiResponse(
        data=await service.release_check(request),
        request_id=get_request_id(),
    )
