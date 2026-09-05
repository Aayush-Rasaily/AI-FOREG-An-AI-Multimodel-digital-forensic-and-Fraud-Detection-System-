"""Phase 9F evidence integrity monitoring endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_integrity_monitor_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.integrity.schemas import (
    IntegrityAlertListResponse,
    IntegrityDriftListResponse,
    IntegrityHistoryResponse,
    IntegrityPreviewResponse,
    IntegrityRunResponse,
)
from backend.app.integrity.service import IntegrityMonitorService

router = APIRouter(tags=["integrity"])
ServiceDependency = Annotated[
    IntegrityMonitorService,
    Depends(get_integrity_monitor_service),
]


@router.post(
    "/cases/{case_id}/integrity-check",
    response_model=ApiResponse[IntegrityRunResponse],
)
async def run_integrity_check(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntegrityRunResponse]:
    data = await service.generate(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/integrity/preview",
    response_model=ApiResponse[IntegrityPreviewResponse],
)
async def preview_integrity(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntegrityPreviewResponse]:
    data = await service.preview(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/integrity/latest",
    response_model=ApiResponse[IntegrityRunResponse],
)
async def get_latest_integrity(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntegrityRunResponse]:
    data = await service.get_latest(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/integrity",
    response_model=ApiResponse[IntegrityRunResponse],
)
async def get_case_integrity(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntegrityRunResponse]:
    data = await service.get_latest(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/integrity/alerts",
    response_model=ApiResponse[IntegrityAlertListResponse],
)
async def list_integrity_alerts(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntegrityAlertListResponse]:
    data = await service.list_alerts(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/integrity/drift",
    response_model=ApiResponse[IntegrityDriftListResponse],
)
async def list_integrity_drift(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntegrityDriftListResponse]:
    data = await service.list_drifts(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/integrity/history",
    response_model=ApiResponse[IntegrityHistoryResponse],
)
async def get_integrity_history(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntegrityHistoryResponse]:
    data = await service.history(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/integrity/{run_id}",
    response_model=ApiResponse[IntegrityRunResponse],
)
async def get_integrity_run(
    run_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntegrityRunResponse]:
    data = await service.get_run(run_id)
    return ApiResponse(data=data, request_id=get_request_id())
