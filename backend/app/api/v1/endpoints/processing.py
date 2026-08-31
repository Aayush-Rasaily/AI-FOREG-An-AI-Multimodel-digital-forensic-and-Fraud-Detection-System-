"""Version-one asynchronous-ready processing endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.api.dependencies import get_processing_orchestrator
from backend.app.api.schemas.processing import (
    ArtifactListResponse,
    ProcessingJobListResponse,
    ProcessingJobResponse,
)
from backend.app.application.services.processing_service import (
    ProcessingOrchestrator,
)
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["processing"])
OrchestratorDependency = Annotated[
    ProcessingOrchestrator,
    Depends(get_processing_orchestrator),
]


@router.post(
    "/evidence/{evidence_id}/process",
    response_model=ApiResponse[ProcessingJobResponse],
    status_code=202,
    summary="Queue evidence processing",
)
async def process_evidence(
    evidence_id: UUID,
    background_tasks: BackgroundTasks,
    service: OrchestratorDependency,
) -> ApiResponse[ProcessingJobResponse]:
    """Queue deterministic inspection and derivative generation."""

    job = await service.create_job(evidence_id)
    background_tasks.add_task(service.run, job.id)
    return ApiResponse(data=job, request_id=get_request_id())


@router.get(
    "/evidence/{evidence_id}/processing",
    response_model=ApiResponse[ProcessingJobListResponse],
    summary="List evidence processing jobs",
)
async def list_processing_jobs(
    evidence_id: UUID,
    service: OrchestratorDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ProcessingJobListResponse]:
    """Return bounded processing history for one evidence item."""

    return ApiResponse(
        data=await service.list_jobs(evidence_id, limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/processing/{job_id}",
    response_model=ApiResponse[ProcessingJobResponse],
    summary="Retrieve a processing job",
)
async def get_processing_job(
    job_id: UUID,
    service: OrchestratorDependency,
) -> ApiResponse[ProcessingJobResponse]:
    """Retrieve one processing job by UUID."""

    return ApiResponse(
        data=await service.get_job(job_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/artifacts",
    response_model=ApiResponse[ArtifactListResponse],
    summary="List derived evidence artifacts",
)
async def list_evidence_artifacts(
    evidence_id: UUID,
    service: OrchestratorDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ArtifactListResponse]:
    """Return derived artifact metadata without filesystem paths."""

    return ApiResponse(
        data=await service.list_artifacts(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )
