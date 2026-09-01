"""Version-one reference comparison endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.api.dependencies import get_comparison_service
from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.comparison.schemas import (
    CompareRequest,
    ComparisonRunListResponse,
    ComparisonRunResponse,
    ComparisonSummaryResponse,
    DifferenceListResponse,
    ReferenceEvidenceCreateRequest,
    ReferenceEvidenceListResponse,
    ReferenceEvidenceResponse,
)
from backend.app.comparison.service import ComparisonService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["comparison"])
ComparisonServiceDependency = Annotated[
    ComparisonService,
    Depends(get_comparison_service),
]


@router.post(
    "/cases/{case_id}/references",
    response_model=ApiResponse[ReferenceEvidenceResponse],
    status_code=201,
    summary="Register trusted reference evidence",
)
async def register_reference(
    case_id: UUID,
    payload: ReferenceEvidenceCreateRequest,
    service: ComparisonServiceDependency,
) -> ApiResponse[ReferenceEvidenceResponse]:
    """Register processed evidence as immutable trusted reference."""

    return ApiResponse(
        data=await service.register_reference(case_id, payload),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/references",
    response_model=ApiResponse[ReferenceEvidenceListResponse],
    summary="List trusted reference evidence",
)
async def list_references(
    case_id: UUID,
    service: ComparisonServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ReferenceEvidenceListResponse]:
    """Return trusted references registered for one case."""

    return ApiResponse(
        data=await service.list_references(case_id, limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.post(
    "/evidence/{evidence_id}/compare",
    response_model=ApiResponse[ProcessingJobResponse],
    status_code=202,
    summary="Compare evidence against reference",
)
async def compare_evidence(
    evidence_id: UUID,
    payload: CompareRequest,
    background_tasks: BackgroundTasks,
    service: ComparisonServiceDependency,
) -> ApiResponse[ProcessingJobResponse]:
    """Queue reference comparison without modifying original evidence."""

    job = await service.create_job(evidence_id, payload.reference_evidence_id)
    background_tasks.add_task(service.run, job.id)
    return ApiResponse(data=job, request_id=get_request_id())


@router.get(
    "/evidence/{evidence_id}/comparisons",
    response_model=ApiResponse[ComparisonRunListResponse],
    summary="List comparison history",
)
async def list_comparisons(
    evidence_id: UUID,
    service: ComparisonServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ComparisonRunListResponse]:
    """Return comparison run history for one evidence item."""

    return ApiResponse(
        data=await service.list_comparisons(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/comparisons/{comparison_id}",
    response_model=ApiResponse[ComparisonRunResponse],
    summary="Retrieve one comparison run",
)
async def get_comparison(
    comparison_id: UUID,
    service: ComparisonServiceDependency,
) -> ApiResponse[ComparisonRunResponse]:
    """Return one reference comparison run."""

    return ApiResponse(
        data=await service.get_comparison(comparison_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/differences",
    response_model=ApiResponse[DifferenceListResponse],
    summary="List comparison differences",
)
async def list_differences(
    evidence_id: UUID,
    service: ComparisonServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[DifferenceListResponse]:
    """Return persisted comparison differences for one evidence item."""

    return ApiResponse(
        data=await service.list_differences(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/comparison-summary",
    response_model=ApiResponse[ComparisonSummaryResponse],
    summary="Retrieve latest comparison summary",
)
async def get_comparison_summary(
    evidence_id: UUID,
    service: ComparisonServiceDependency,
) -> ApiResponse[ComparisonSummaryResponse]:
    """Return the latest reference comparison summary."""

    return ApiResponse(
        data=await service.get_summary(evidence_id),
        request_id=get_request_id(),
    )
