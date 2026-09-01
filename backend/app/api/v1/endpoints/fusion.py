"""Version-one multimodal fusion and AI jury endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.api.dependencies import get_fusion_service
from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.fusion.schemas import (
    FusionAnalysisDetailResponse,
    FusionAnalysisRunListResponse,
    FusionConflictResponse,
    FusionSignalsResponse,
    JuryAssessmentResponse,
)
from backend.app.fusion.service import FusionService

router = APIRouter(tags=["fusion"])
FusionServiceDependency = Annotated[FusionService, Depends(get_fusion_service)]


@router.post(
    "/evidence/{evidence_id}/fusion-analysis",
    response_model=ApiResponse[ProcessingJobResponse],
    status_code=202,
    summary="Queue multimodal fusion analysis",
)
async def analyze_fusion_evidence(
    evidence_id: UUID,
    background_tasks: BackgroundTasks,
    service: FusionServiceDependency,
) -> ApiResponse[ProcessingJobResponse]:
    """Queue multimodal evidence fusion without re-running modality analyzers."""

    job = await service.create_job(evidence_id)
    background_tasks.add_task(service.run, job.id)
    return ApiResponse(data=job, request_id=get_request_id())


@router.get(
    "/evidence/{evidence_id}/fusion-analysis",
    response_model=ApiResponse[FusionAnalysisRunListResponse],
    summary="List multimodal fusion analysis history",
)
async def list_fusion_analysis_runs(
    evidence_id: UUID,
    service: FusionServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[FusionAnalysisRunListResponse]:
    """Return multimodal fusion analysis history for one evidence item."""

    return ApiResponse(
        data=await service.list_runs(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/fusion-analysis/latest",
    response_model=ApiResponse[FusionAnalysisDetailResponse],
    summary="Retrieve latest multimodal fusion assessment",
)
async def get_latest_fusion_analysis(
    evidence_id: UUID,
    service: FusionServiceDependency,
) -> ApiResponse[FusionAnalysisDetailResponse]:
    """Return the most recent multimodal fusion assessment for one evidence item."""

    return ApiResponse(
        data=await service.get_latest(evidence_id),
        request_id=get_request_id(),
    )


@router.get(
    "/fusion-analysis/{analysis_id}",
    response_model=ApiResponse[FusionAnalysisDetailResponse],
    summary="Retrieve one multimodal fusion analysis run",
)
async def get_fusion_analysis_run(
    analysis_id: UUID,
    service: FusionServiceDependency,
) -> ApiResponse[FusionAnalysisDetailResponse]:
    """Return one persisted multimodal fusion analysis run."""

    return ApiResponse(
        data=await service.get_run(analysis_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/fusion-jury",
    response_model=ApiResponse[list[JuryAssessmentResponse]],
    summary="List jury assessments for latest fusion run",
)
async def list_fusion_jury(
    evidence_id: UUID,
    service: FusionServiceDependency,
) -> ApiResponse[list[JuryAssessmentResponse]]:
    """Return jury member assessments from the latest fusion analysis."""

    return ApiResponse(
        data=await service.list_jury(evidence_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/fusion-conflicts",
    response_model=ApiResponse[list[FusionConflictResponse]],
    summary="List conflicts for latest fusion run",
)
async def list_fusion_conflicts(
    evidence_id: UUID,
    service: FusionServiceDependency,
) -> ApiResponse[list[FusionConflictResponse]]:
    """Return cross-modal conflicts from the latest fusion analysis."""

    return ApiResponse(
        data=await service.list_conflicts(evidence_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/fusion-signals",
    response_model=ApiResponse[FusionSignalsResponse],
    summary="Preview normalized fusion signals",
)
async def get_fusion_signals(
    evidence_id: UUID,
    service: FusionServiceDependency,
) -> ApiResponse[FusionSignalsResponse]:
    """Return normalized findings and modality availability without persisting."""

    return ApiResponse(
        data=await service.get_signals(evidence_id),
        request_id=get_request_id(),
    )
