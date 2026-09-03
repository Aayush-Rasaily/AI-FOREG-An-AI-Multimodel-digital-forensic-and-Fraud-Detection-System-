"""Version-one cross-evidence correlation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.api.dependencies import get_correlation_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.correlation.schemas import (
    CorrelationDetailResponse,
    CorrelationRunListResponse,
    CorrelationRunResponse,
    EvidenceCorrelationResponse,
)
from backend.app.correlation.service import CorrelationService

router = APIRouter(tags=["correlation"])
CorrelationServiceDependency = Annotated[
    CorrelationService,
    Depends(get_correlation_service),
]


@router.post(
    "/cases/{case_id}/correlations",
    response_model=ApiResponse[CorrelationRunResponse],
    status_code=202,
    summary="Queue cross-evidence correlation analysis",
)
async def create_correlations(
    case_id: UUID,
    background_tasks: BackgroundTasks,
    service: CorrelationServiceDependency,
) -> ApiResponse[CorrelationRunResponse]:
    """Queue deterministic correlation discovery for one case."""

    run = await service.create_analysis(case_id)
    background_tasks.add_task(service.run, run.id)
    return ApiResponse(data=run, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/correlations",
    response_model=ApiResponse[CorrelationRunListResponse],
    summary="List correlation analysis history",
)
async def list_case_correlations(
    case_id: UUID,
    service: CorrelationServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[CorrelationRunListResponse]:
    """Return correlation analysis history for one case."""

    return ApiResponse(
        data=await service.list_runs(case_id, limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/correlations/latest",
    response_model=ApiResponse[CorrelationDetailResponse],
    summary="Retrieve latest correlation analysis",
)
async def get_latest_correlations(
    case_id: UUID,
    service: CorrelationServiceDependency,
) -> ApiResponse[CorrelationDetailResponse]:
    """Return the most recent correlation analysis with relationships."""

    return ApiResponse(
        data=await service.get_latest(case_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/correlations",
    response_model=ApiResponse[list[EvidenceCorrelationResponse]],
    summary="List correlations involving one evidence item",
)
async def list_evidence_correlations(
    evidence_id: UUID,
    service: CorrelationServiceDependency,
) -> ApiResponse[list[EvidenceCorrelationResponse]]:
    """Return latest-run correlations that involve one evidence item."""

    return ApiResponse(
        data=await service.list_for_evidence(evidence_id),
        request_id=get_request_id(),
    )


@router.get(
    "/correlations/{correlation_id}",
    response_model=ApiResponse[EvidenceCorrelationResponse],
    summary="Retrieve one evidence correlation",
)
async def get_correlation(
    correlation_id: UUID,
    service: CorrelationServiceDependency,
) -> ApiResponse[EvidenceCorrelationResponse]:
    """Return one persisted evidence correlation."""

    return ApiResponse(
        data=await service.get_correlation(correlation_id),
        request_id=get_request_id(),
    )
