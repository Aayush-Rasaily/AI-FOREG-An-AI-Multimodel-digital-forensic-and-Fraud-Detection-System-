"""Version-one AI image forensic analysis endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.ai.image.schemas import (
    ImageAIFindingListResponse,
    ImageAnalysisRunListResponse,
    ImageAnalysisRunResponse,
)
from backend.app.ai.image.service import ImageAnalysisService
from backend.app.api.dependencies import get_image_analysis_service
from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["image-ai"])
ImageAnalysisServiceDependency = Annotated[
    ImageAnalysisService,
    Depends(get_image_analysis_service),
]


@router.post(
    "/evidence/{evidence_id}/image-analysis",
    response_model=ApiResponse[ProcessingJobResponse],
    status_code=202,
    summary="Queue AI image forensic analysis",
)
async def analyze_image_evidence(
    evidence_id: UUID,
    background_tasks: BackgroundTasks,
    service: ImageAnalysisServiceDependency,
) -> ApiResponse[ProcessingJobResponse]:
    """Queue AI image analysis without modifying original evidence."""

    job = await service.create_job(evidence_id)
    background_tasks.add_task(service.run, job.id)
    return ApiResponse(data=job, request_id=get_request_id())


@router.get(
    "/evidence/{evidence_id}/image-analysis",
    response_model=ApiResponse[ImageAnalysisRunListResponse],
    summary="List AI image analysis history",
)
async def list_image_analysis_runs(
    evidence_id: UUID,
    service: ImageAnalysisServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ImageAnalysisRunListResponse]:
    """Return AI image analysis history for one evidence item."""

    return ApiResponse(
        data=await service.list_runs(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/image-analysis/{analysis_id}",
    response_model=ApiResponse[ImageAnalysisRunResponse],
    summary="Retrieve one AI image analysis run",
)
async def get_image_analysis_run(
    analysis_id: UUID,
    service: ImageAnalysisServiceDependency,
) -> ApiResponse[ImageAnalysisRunResponse]:
    """Return one AI image analysis run."""

    return ApiResponse(
        data=await service.get_run(analysis_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/image-findings",
    response_model=ApiResponse[ImageAIFindingListResponse],
    summary="List AI image findings",
)
async def list_image_findings(
    evidence_id: UUID,
    service: ImageAnalysisServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    detector: Annotated[str | None, Query()] = None,
) -> ApiResponse[ImageAIFindingListResponse]:
    """Return persisted AI image findings for one evidence item."""

    return ApiResponse(
        data=await service.list_findings(
            evidence_id,
            limit=limit,
            offset=offset,
            detector=detector,
        ),
        request_id=get_request_id(),
    )
