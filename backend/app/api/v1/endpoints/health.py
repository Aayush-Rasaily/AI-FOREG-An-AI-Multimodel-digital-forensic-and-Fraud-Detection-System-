"""Process liveness endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_db_session
from backend.app.api.schemas.health import HealthResponse, LivenessResponse
from backend.app.application.services.health_service import check_database_health
from backend.app.core.config import Settings
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(prefix="/health", tags=["health"])
database_session_dependency = Depends(get_db_session)


@router.get(
    "",
    response_model=ApiResponse[HealthResponse],
    summary="Check application health",
)
async def read_health(
    request: Request,
    session: AsyncSession = database_session_dependency,
) -> ApiResponse[HealthResponse]:
    """Return application health without making startup depend on PostgreSQL."""

    settings: Settings = request.app.state.settings
    database_healthy = await check_database_health(
        session,
        timeout_seconds=settings.db_health_timeout_seconds,
    )
    return ApiResponse(
        data=HealthResponse(
            status="healthy" if database_healthy else "degraded",
            version=settings.app_version,
            environment=settings.app_env,
            database="healthy" if database_healthy else "unavailable",
            timestamp=datetime.now(UTC),
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/live",
    response_model=ApiResponse[LivenessResponse],
    summary="Check process liveness",
)
async def read_liveness(request: Request) -> ApiResponse[LivenessResponse]:
    """Return a process-level liveness signal without network dependencies."""

    settings: Settings = request.app.state.settings
    return ApiResponse(
        data=LivenessResponse(
            service=settings.app_name,
            version=settings.app_version,
        ),
        request_id=get_request_id(),
    )
