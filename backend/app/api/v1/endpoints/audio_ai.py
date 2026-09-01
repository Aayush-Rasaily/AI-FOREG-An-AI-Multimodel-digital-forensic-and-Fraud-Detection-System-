"""Version-one AI audio forensic analysis endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.ai.audio.schemas import (
    AudioAIFindingListResponse,
    AudioAnalysisDetailResponse,
    AudioAnalysisRequest,
    AudioAnalysisRunListResponse,
    AudioFeatureSummaryResponse,
    AudioSegmentResponse,
    AudioTimelineEntryResponse,
)
from backend.app.ai.audio.service import AudioAnalysisService
from backend.app.api.dependencies import get_audio_analysis_service
from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["audio-ai"])
AudioAnalysisServiceDependency = Annotated[
    AudioAnalysisService,
    Depends(get_audio_analysis_service),
]


@router.post(
    "/evidence/{evidence_id}/audio-analysis",
    response_model=ApiResponse[ProcessingJobResponse],
    status_code=202,
    summary="Queue AI audio forensic analysis",
)
async def analyze_audio_evidence(
    evidence_id: UUID,
    background_tasks: BackgroundTasks,
    service: AudioAnalysisServiceDependency,
    body: AudioAnalysisRequest | None = None,
) -> ApiResponse[ProcessingJobResponse]:
    """Queue AI audio analysis without modifying original evidence."""

    reference_id = body.reference_evidence_id if body else None
    job = await service.create_job(
        evidence_id,
        reference_evidence_id=reference_id,
    )
    background_tasks.add_task(service.run, job.id)
    return ApiResponse(data=job, request_id=get_request_id())


@router.get(
    "/evidence/{evidence_id}/audio-analysis",
    response_model=ApiResponse[AudioAnalysisRunListResponse],
    summary="List AI audio analysis history",
)
async def list_audio_analysis_runs(
    evidence_id: UUID,
    service: AudioAnalysisServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[AudioAnalysisRunListResponse]:
    """Return AI audio analysis history for one evidence item."""

    return ApiResponse(
        data=await service.list_runs(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/audio-analysis/{analysis_id}",
    response_model=ApiResponse[AudioAnalysisDetailResponse],
    summary="Retrieve one AI audio analysis run",
)
async def get_audio_analysis_run(
    analysis_id: UUID,
    service: AudioAnalysisServiceDependency,
) -> ApiResponse[AudioAnalysisDetailResponse]:
    """Return one AI audio analysis run with timeline and features."""

    return ApiResponse(
        data=await service.get_run_detail(analysis_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/audio-findings",
    response_model=ApiResponse[AudioAIFindingListResponse],
    summary="List AI audio findings",
)
async def list_audio_findings(
    evidence_id: UUID,
    service: AudioAnalysisServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    detector: Annotated[str | None, Query()] = None,
) -> ApiResponse[AudioAIFindingListResponse]:
    """Return persisted AI audio findings for one evidence item."""

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
    "/audio-analysis/{analysis_id}/timeline",
    response_model=ApiResponse[list[AudioTimelineEntryResponse]],
    summary="List timeline entries for one analysis run",
)
async def list_audio_analysis_timeline(
    analysis_id: UUID,
    service: AudioAnalysisServiceDependency,
) -> ApiResponse[list[AudioTimelineEntryResponse]]:
    """Return temporal timeline entries for one analysis run."""

    return ApiResponse(
        data=await service.list_timeline(analysis_id),
        request_id=get_request_id(),
    )


@router.get(
    "/audio-analysis/{analysis_id}/segments",
    response_model=ApiResponse[list[AudioSegmentResponse]],
    summary="List localized segments for one analysis run",
)
async def list_audio_analysis_segments(
    analysis_id: UUID,
    service: AudioAnalysisServiceDependency,
) -> ApiResponse[list[AudioSegmentResponse]]:
    """Return localized segment summaries for one analysis run."""

    return ApiResponse(
        data=await service.list_segments(analysis_id),
        request_id=get_request_id(),
    )


@router.get(
    "/audio-analysis/{analysis_id}/features",
    response_model=ApiResponse[AudioFeatureSummaryResponse | None],
    summary="Retrieve feature summary for one analysis run",
)
async def get_audio_analysis_features(
    analysis_id: UUID,
    service: AudioAnalysisServiceDependency,
) -> ApiResponse[AudioFeatureSummaryResponse | None]:
    """Return deterministic feature summary for one analysis run."""

    return ApiResponse(
        data=await service.get_features(analysis_id),
        request_id=get_request_id(),
    )
