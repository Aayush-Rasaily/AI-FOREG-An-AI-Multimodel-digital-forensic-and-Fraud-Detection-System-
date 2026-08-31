"""Version-one case management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from backend.app.api.dependencies import get_case_service
from backend.app.api.schemas.case import (
    CaseCreateRequest,
    CaseListResponse,
    CaseResponse,
    CaseUpdateRequest,
)
from backend.app.application.services.case_service import CaseService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(prefix="/cases", tags=["cases"])
CaseServiceDependency = Annotated[CaseService, Depends(get_case_service)]


@router.post(
    "",
    response_model=ApiResponse[CaseResponse],
    status_code=201,
    summary="Create an investigation case",
)
async def create_case(
    payload: CaseCreateRequest,
    service: CaseServiceDependency,
) -> ApiResponse[CaseResponse]:
    """Create a server-numbered case."""

    return ApiResponse(data=await service.create(payload), request_id=get_request_id())


@router.get(
    "",
    response_model=ApiResponse[CaseListResponse],
    summary="List investigation cases",
)
async def list_cases(
    service: CaseServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[CaseListResponse]:
    """Return a bounded page of cases."""

    return ApiResponse(
        data=await service.list(limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/{case_id}",
    response_model=ApiResponse[CaseResponse],
    summary="Retrieve an investigation case",
)
async def get_case(
    case_id: UUID,
    service: CaseServiceDependency,
) -> ApiResponse[CaseResponse]:
    """Retrieve one case by internal UUID."""

    return ApiResponse(data=await service.get(case_id), request_id=get_request_id())


@router.patch(
    "/{case_id}",
    response_model=ApiResponse[CaseResponse],
    summary="Update an investigation case",
)
async def update_case(
    case_id: UUID,
    payload: CaseUpdateRequest,
    service: CaseServiceDependency,
) -> ApiResponse[CaseResponse]:
    """Apply safe mutable updates to one case."""

    return ApiResponse(
        data=await service.update(case_id, payload),
        request_id=get_request_id(),
    )
