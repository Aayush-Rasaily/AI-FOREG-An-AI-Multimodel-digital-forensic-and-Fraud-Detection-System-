"""Version-one investigation intelligence endpoints (Phase 8C).

Uses `/investigation-summaries` paths to preserve Phase 6G
`/cases/{id}/intelligence` APIs unchanged.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from backend.app.api.dependencies import get_intelligence_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.intelligence.schemas import (
    InvestigationSummaryListResponse,
    InvestigationSummaryResponse,
)
from backend.app.intelligence.service import InvestigationIntelligenceService

router = APIRouter(tags=["investigation-intelligence"])
IntelligenceServiceDependency = Annotated[
    InvestigationIntelligenceService,
    Depends(get_intelligence_service),
]


@router.post(
    "/cases/{case_id}/investigation-summaries",
    response_model=ApiResponse[InvestigationSummaryResponse],
    status_code=201,
    summary="Generate investigation intelligence summary",
)
async def generate_investigation_summary(
    case_id: UUID,
    service: IntelligenceServiceDependency,
) -> ApiResponse[InvestigationSummaryResponse]:
    """Synthesize a deterministic case narrative from stored outputs."""

    return ApiResponse(
        data=await service.generate(case_id),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/investigation-summaries",
    response_model=ApiResponse[InvestigationSummaryListResponse],
    summary="List investigation intelligence summaries",
)
async def list_investigation_summaries(
    case_id: UUID,
    service: IntelligenceServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[InvestigationSummaryListResponse]:
    """Return investigation summary history for a case."""

    return ApiResponse(
        data=await service.list_summaries(case_id, limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/investigation-summaries/latest",
    response_model=ApiResponse[InvestigationSummaryResponse],
    summary="Retrieve latest investigation intelligence summary",
)
async def get_latest_investigation_summary(
    case_id: UUID,
    service: IntelligenceServiceDependency,
) -> ApiResponse[InvestigationSummaryResponse]:
    """Return the most recent investigation summary for a case."""

    return ApiResponse(
        data=await service.get_latest(case_id),
        request_id=get_request_id(),
    )


@router.get(
    "/investigation-summaries/{summary_id}",
    response_model=ApiResponse[InvestigationSummaryResponse],
    summary="Retrieve a single investigation intelligence summary",
)
async def get_investigation_summary(
    summary_id: UUID,
    service: IntelligenceServiceDependency,
) -> ApiResponse[InvestigationSummaryResponse]:
    """Return one persisted investigation summary by id."""

    return ApiResponse(
        data=await service.get_summary(summary_id),
        request_id=get_request_id(),
    )
