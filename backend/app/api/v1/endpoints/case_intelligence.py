"""Version-one case intelligence endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.api.dependencies import get_case_intelligence_service
from backend.app.case_intelligence.schemas import (
    CaseConflictResponse,
    CaseIntelligenceDetailResponse,
    CaseIntelligenceRunListResponse,
    CaseIntelligenceRunResponse,
    CaseRelationshipResponse,
    TimelineEventResponse,
)
from backend.app.case_intelligence.service import CaseIntelligenceService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["case-intelligence"])
CaseIntelligenceServiceDependency = Annotated[
    CaseIntelligenceService,
    Depends(get_case_intelligence_service),
]


@router.post(
    "/cases/{case_id}/intelligence",
    response_model=ApiResponse[CaseIntelligenceRunResponse],
    status_code=202,
    summary="Queue case-level forensic intelligence synthesis",
)
async def analyze_case_intelligence(
    case_id: UUID,
    background_tasks: BackgroundTasks,
    service: CaseIntelligenceServiceDependency,
) -> ApiResponse[CaseIntelligenceRunResponse]:
    """Queue case-level synthesis using existing Phase 6F fusion results."""

    run = await service.create_analysis(case_id)
    background_tasks.add_task(service.run, run.id)
    return ApiResponse(data=run, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/intelligence",
    response_model=ApiResponse[CaseIntelligenceRunListResponse],
    summary="List case intelligence analysis history",
)
async def list_case_intelligence_runs(
    case_id: UUID,
    service: CaseIntelligenceServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[CaseIntelligenceRunListResponse]:
    """Return case intelligence analysis history."""

    return ApiResponse(
        data=await service.list_runs(case_id, limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/intelligence/latest",
    response_model=ApiResponse[CaseIntelligenceDetailResponse],
    summary="Retrieve latest case intelligence assessment",
)
async def get_latest_case_intelligence(
    case_id: UUID,
    service: CaseIntelligenceServiceDependency,
) -> ApiResponse[CaseIntelligenceDetailResponse]:
    """Return the most recent case intelligence assessment."""

    return ApiResponse(
        data=await service.get_latest(case_id),
        request_id=get_request_id(),
    )


@router.get(
    "/case-intelligence/{analysis_id}",
    response_model=ApiResponse[CaseIntelligenceDetailResponse],
    summary="Retrieve one case intelligence run",
)
async def get_case_intelligence_run(
    analysis_id: UUID,
    service: CaseIntelligenceServiceDependency,
) -> ApiResponse[CaseIntelligenceDetailResponse]:
    """Return one persisted case intelligence run."""

    return ApiResponse(
        data=await service.get_run(analysis_id),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/relationships",
    response_model=ApiResponse[list[CaseRelationshipResponse]],
    summary="List cross-evidence relationships for latest case run",
)
async def list_case_relationships(
    case_id: UUID,
    service: CaseIntelligenceServiceDependency,
) -> ApiResponse[list[CaseRelationshipResponse]]:
    """Return relationships from the latest case intelligence analysis."""

    return ApiResponse(
        data=await service.list_relationships(case_id),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/conflicts",
    response_model=ApiResponse[list[CaseConflictResponse]],
    summary="List case-level conflicts for latest run",
)
async def list_case_conflicts(
    case_id: UUID,
    service: CaseIntelligenceServiceDependency,
) -> ApiResponse[list[CaseConflictResponse]]:
    """Return conflicts from the latest case intelligence analysis."""

    return ApiResponse(
        data=await service.list_conflicts(case_id),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/timeline",
    response_model=ApiResponse[list[TimelineEventResponse]],
    summary="List case timeline for latest run",
)
async def list_case_timeline(
    case_id: UUID,
    service: CaseIntelligenceServiceDependency,
) -> ApiResponse[list[TimelineEventResponse]]:
    """Return timeline events from the latest case intelligence analysis."""

    return ApiResponse(
        data=await service.list_timeline(case_id),
        request_id=get_request_id(),
    )
