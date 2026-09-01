"""Version-one forensic analysis endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.api.dependencies import get_forensic_service
from backend.app.api.schemas.processing import (
    ArtifactListResponse,
    ProcessingJobResponse,
)
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.forensics.schemas import (
    AnalysisRunListResponse,
    AnalysisRunResponse,
    AnalysisSummaryResponse,
    FindingListResponse,
)
from backend.app.forensics.service import ForensicAnalysisService

router = APIRouter(tags=["forensics"])
ForensicServiceDependency = Annotated[
    ForensicAnalysisService,
    Depends(get_forensic_service),
]


@router.post(
    "/evidence/{evidence_id}/analyze",
    response_model=ApiResponse[ProcessingJobResponse],
    status_code=202,
    summary="Queue forensic analysis",
)
async def analyze_evidence(
    evidence_id: UUID,
    background_tasks: BackgroundTasks,
    service: ForensicServiceDependency,
) -> ApiResponse[ProcessingJobResponse]:
    """Queue deterministic forensic analysis without modifying original evidence."""

    job = await service.create_job(evidence_id)
    background_tasks.add_task(service.run, job.id)
    return ApiResponse(data=job, request_id=get_request_id())


@router.get(
    "/evidence/{evidence_id}/analysis",
    response_model=ApiResponse[AnalysisRunListResponse],
    summary="List forensic analysis history",
)
async def list_analysis_runs(
    evidence_id: UUID,
    service: ForensicServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[AnalysisRunListResponse]:
    """Return analysis run history for one evidence item."""

    return ApiResponse(
        data=await service.list_analysis_runs(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/analysis/{analysis_id}",
    response_model=ApiResponse[AnalysisRunResponse],
    summary="Retrieve one analysis run",
)
async def get_analysis_run(
    analysis_id: UUID,
    service: ForensicServiceDependency,
) -> ApiResponse[AnalysisRunResponse]:
    """Return one forensic analysis run."""

    return ApiResponse(
        data=await service.get_analysis_run(analysis_id),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/findings",
    response_model=ApiResponse[FindingListResponse],
    summary="List forensic findings",
)
async def list_findings(
    evidence_id: UUID,
    service: ForensicServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[FindingListResponse]:
    """Return persisted forensic findings for one evidence item."""

    return ApiResponse(
        data=await service.list_findings(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/heatmaps",
    response_model=ApiResponse[ArtifactListResponse],
    summary="List forensic visualization artifacts",
)
async def list_heatmaps(
    evidence_id: UUID,
    service: ForensicServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ArtifactListResponse]:
    """Return ELA images, heatmaps, masks, and overlays."""

    return ApiResponse(
        data=await service.list_heatmaps(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/analysis-summary",
    response_model=ApiResponse[AnalysisSummaryResponse],
    summary="Retrieve latest analysis summary",
)
async def get_analysis_summary(
    evidence_id: UUID,
    service: ForensicServiceDependency,
) -> ApiResponse[AnalysisSummaryResponse]:
    """Return the latest forensic analysis summary."""

    return ApiResponse(
        data=await service.get_summary(evidence_id),
        request_id=get_request_id(),
    )
