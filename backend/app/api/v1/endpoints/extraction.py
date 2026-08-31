"""Version-one extraction and localization endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.api.dependencies import get_extraction_service
from backend.app.api.schemas.processing import (
    ArtifactListResponse,
    ProcessingJobResponse,
)
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.extraction.models import ExtractionType
from backend.app.extraction.schemas import ExtractionListResponse, ExtractionResponse
from backend.app.extraction.service import ExtractionService

router = APIRouter(tags=["extraction"])
ExtractionServiceDependency = Annotated[
    ExtractionService,
    Depends(get_extraction_service),
]


@router.post(
    "/evidence/{evidence_id}/extract",
    response_model=ApiResponse[ProcessingJobResponse],
    status_code=202,
    summary="Queue evidence extraction",
)
async def extract_evidence(
    evidence_id: UUID,
    background_tasks: BackgroundTasks,
    service: ExtractionServiceDependency,
) -> ApiResponse[ProcessingJobResponse]:
    """Queue structured extraction without changing the original evidence."""

    job = await service.create_job(evidence_id)
    background_tasks.add_task(service.run, job.id)
    return ApiResponse(data=job, request_id=get_request_id())


@router.get(
    "/evidence/{evidence_id}/extractions",
    response_model=ApiResponse[ExtractionListResponse],
    summary="List evidence extractions",
)
async def list_extractions(
    evidence_id: UUID,
    service: ExtractionServiceDependency,
    extraction_type: ExtractionType | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ExtractionListResponse]:
    """Return source-linked extracted records and capability status."""

    return ApiResponse(
        data=await service.list_extractions(
            evidence_id,
            extraction_type=extraction_type,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/extractions/{extraction_id}",
    response_model=ApiResponse[ExtractionResponse],
    summary="Retrieve one extraction",
)
async def get_extraction(
    evidence_id: UUID,
    extraction_id: UUID,
    service: ExtractionServiceDependency,
) -> ApiResponse[ExtractionResponse]:
    """Retrieve one extraction while validating its evidence scope."""

    return ApiResponse(
        data=await service.get_extraction(evidence_id, extraction_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/regions",
    response_model=ApiResponse[ExtractionListResponse],
    summary="List localized extraction regions",
)
async def list_regions(
    evidence_id: UUID,
    service: ExtractionServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ExtractionListResponse]:
    """Return only detector-backed or parser-backed localized regions."""

    return ApiResponse(
        data=await service.list_regions(evidence_id, limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/extraction-artifacts",
    response_model=ApiResponse[ArtifactListResponse],
    summary="List extraction artifacts",
)
async def list_extraction_artifacts(
    evidence_id: UUID,
    service: ExtractionServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ArtifactListResponse]:
    """Return metadata for extraction-derived artifacts only."""

    return ApiResponse(
        data=await service.list_artifacts(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )
