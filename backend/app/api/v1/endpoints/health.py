"""Prometheus metrics and readiness-related observability endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_db_session
from backend.app.api.schemas.health import (
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
)
from backend.app.application.services.health_service import check_database_health
from backend.app.core.config import Settings
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.monitoring.health import build_readiness_report
from backend.app.monitoring.prometheus import render_prometheus_metrics

health_router = APIRouter(prefix="/health", tags=["health"])
metrics_router = APIRouter(tags=["metrics"])
database_session_dependency = Depends(get_db_session)


@health_router.get(
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


@health_router.get(
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


@health_router.get(
    "/ready",
    response_model=ApiResponse[ReadinessResponse],
    summary="Check process readiness",
)
async def read_readiness(
    request: Request,
    session: AsyncSession = database_session_dependency,
) -> ApiResponse[ReadinessResponse]:
    """Return readiness based on DB, Redis, storage, AI, disk, and memory."""

    settings: Settings = request.app.state.settings
    report = await build_readiness_report(
        settings=settings,
        session=session,
        app_state=request.app.state,
    )
    return ApiResponse(
        data=ReadinessResponse(
            status=report["status"],
            ready=bool(report["ready"]),
            checks=list(report["checks"]),
            fail_count=int(report["fail_count"]),
            environment=str(report["environment"]),
            version=str(report["version"]),
            timestamp=datetime.now(UTC),
        ),
        request_id=get_request_id(),
    )


@metrics_router.get(
    "/metrics",
    summary="Prometheus metrics exposition",
    include_in_schema=False,
)
async def prometheus_metrics() -> Response:
    """Expose Prometheus text metrics (no authentication)."""

    payload, content_type = render_prometheus_metrics()
    return Response(content=payload, media_type=content_type)


# Backward-compatible aliases used by the previous health module import path.
router = health_router
