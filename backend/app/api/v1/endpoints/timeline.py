"""Version-one investigation timeline endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.api.dependencies import get_timeline_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.timeline.schemas import (
    TimelineConflictResponse,
    TimelineDetailResponse,
    TimelineRunListResponse,
    TimelineRunResponse,
)
from backend.app.timeline.service import TimelineService

router = APIRouter(tags=["timeline"])
TimelineServiceDependency = Annotated[TimelineService, Depends(get_timeline_service)]


@router.post(
    "/cases/{case_id}/timeline",
    response_model=ApiResponse[TimelineRunResponse],
    status_code=202,
    summary="Queue investigation timeline reconstruction",
)
async def create_timeline(
    case_id: UUID,
    background_tasks: BackgroundTasks,
    service: TimelineServiceDependency,
) -> ApiResponse[TimelineRunResponse]:
    """Queue deterministic timeline reconstruction for one case."""

    run = await service.create_timeline(case_id)
    background_tasks.add_task(service.run, run.id)
    return ApiResponse(data=run, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/timeline",
    response_model=ApiResponse[TimelineRunListResponse],
    summary="List investigation timeline history",
)
async def list_case_timelines(
    case_id: UUID,
    service: TimelineServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[TimelineRunListResponse]:
    """Return timeline reconstruction history for one case."""

    return ApiResponse(
        data=await service.list_timelines(case_id, limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/timeline/latest",
    response_model=ApiResponse[TimelineDetailResponse],
    summary="Retrieve latest investigation timeline",
)
async def get_latest_timeline(
    case_id: UUID,
    service: TimelineServiceDependency,
) -> ApiResponse[TimelineDetailResponse]:
    """Return the most recent investigation timeline with events and conflicts."""

    return ApiResponse(
        data=await service.get_latest(case_id),
        request_id=get_request_id(),
    )


@router.get(
    "/timeline/{timeline_id}",
    response_model=ApiResponse[TimelineDetailResponse],
    summary="Retrieve one investigation timeline",
)
async def get_timeline(
    timeline_id: UUID,
    service: TimelineServiceDependency,
) -> ApiResponse[TimelineDetailResponse]:
    """Return one persisted investigation timeline."""

    return ApiResponse(
        data=await service.get_timeline(timeline_id),
        request_id=get_request_id(),
    )


@router.get(
    "/timeline/{timeline_id}/conflicts",
    response_model=ApiResponse[list[TimelineConflictResponse]],
    summary="List timeline conflicts",
)
async def list_timeline_conflicts(
    timeline_id: UUID,
    service: TimelineServiceDependency,
) -> ApiResponse[list[TimelineConflictResponse]]:
    """Return timestamp conflicts for one investigation timeline."""

    return ApiResponse(
        data=await service.list_conflicts(timeline_id),
        request_id=get_request_id(),
    )
