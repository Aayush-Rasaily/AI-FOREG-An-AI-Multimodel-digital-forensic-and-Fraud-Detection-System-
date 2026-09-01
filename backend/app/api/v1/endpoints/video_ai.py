"""Version-one AI video forensic analysis endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.ai.video.schemas import (
    VideoAIFindingListResponse,
    VideoAnalysisDetailResponse,
    VideoAnalysisRunListResponse,
    VideoFrameResponse,
    VideoTimelineEntryResponse,
)
from backend.app.ai.video.service import VideoAnalysisService
from backend.app.api.dependencies import get_video_analysis_service
from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["video-ai"])
VideoAnalysisServiceDependency = Annotated[
    VideoAnalysisService,
    Depends(get_video_analysis_service),
]


@router.post(
    "/evidence/{evidence_id}/video-analysis",
    response_model=ApiResponse[ProcessingJobResponse],
    status_code=202,
    summary="Queue AI video forensic analysis",
)
async def analyze_video_evidence(
    evidence_id: UUID,
    background_tasks: BackgroundTasks,
    service: VideoAnalysisServiceDependency,
) -> ApiResponse[ProcessingJobResponse]:
    """Queue AI video analysis without modifying original evidence."""

    job = await service.create_job(evidence_id)
    background_tasks.add_task(service.run, job.id)
    return ApiResponse(data=job, request_id=get_request_id())


@router.get(
    "/evidence/{evidence_id}/video-analysis",
    response_model=ApiResponse[VideoAnalysisRunListResponse],
    summary="List AI video analysis history",
)
async def list_video_analysis_runs(
    evidence_id: UUID,
    service: VideoAnalysisServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[VideoAnalysisRunListResponse]:
    """Return AI video analysis history for one evidence item."""

    return ApiResponse(
        data=await service.list_runs(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/video-analysis/{analysis_id}",
    response_model=ApiResponse[VideoAnalysisDetailResponse],
    summary="Retrieve one AI video analysis run",
)
async def get_video_analysis_run(
    analysis_id: UUID,
    service: VideoAnalysisServiceDependency,
) -> ApiResponse[VideoAnalysisDetailResponse]:
    """Return one AI video analysis run with timeline and frames."""

    return ApiResponse(
        data=await service.get_run_detail(analysis_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/video-findings",
    response_model=ApiResponse[VideoAIFindingListResponse],
    summary="List AI video findings",
)
async def list_video_findings(
    evidence_id: UUID,
    service: VideoAnalysisServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    detector: Annotated[str | None, Query()] = None,
) -> ApiResponse[VideoAIFindingListResponse]:
    """Return persisted AI video findings for one evidence item."""

    return ApiResponse(
        data=await service.list_findings(
            evidence_id,
            limit=limit,
            offset=offset,
            detector=detector,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/video-analysis/{analysis_id}/frames",
    response_model=ApiResponse[list[VideoFrameResponse]],
    summary="List sampled frames for one analysis run",
)
async def list_video_analysis_frames(
    analysis_id: UUID,
    service: VideoAnalysisServiceDependency,
) -> ApiResponse[list[VideoFrameResponse]]:
    """Return sampled frame references for one analysis run."""

    return ApiResponse(
        data=await service.list_frames(analysis_id),
        request_id=get_request_id(),
    )


@router.get(
    "/video-analysis/{analysis_id}/timeline",
    response_model=ApiResponse[list[VideoTimelineEntryResponse]],
    summary="List timeline entries for one analysis run",
)
async def list_video_analysis_timeline(
    analysis_id: UUID,
    service: VideoAnalysisServiceDependency,
) -> ApiResponse[list[VideoTimelineEntryResponse]]:
    """Return temporal timeline entries for one analysis run."""

    return ApiResponse(
        data=await service.list_timeline(analysis_id),
        request_id=get_request_id(),
    )
