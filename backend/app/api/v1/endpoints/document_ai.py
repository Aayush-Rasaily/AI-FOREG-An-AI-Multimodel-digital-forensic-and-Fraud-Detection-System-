"""Version-one AI document forensic analysis endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.ai.document.schemas import (
    DocumentAIFindingListResponse,
    DocumentAnalysisRunListResponse,
)
from backend.app.ai.document.service import DocumentAnalysisService
from backend.app.api.dependencies import get_document_analysis_service
from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["document-ai"])
DocumentAnalysisServiceDependency = Annotated[
    DocumentAnalysisService,
    Depends(get_document_analysis_service),
]


@router.post(
    "/evidence/{evidence_id}/document-analysis",
    response_model=ApiResponse[ProcessingJobResponse],
    status_code=202,
    summary="Queue AI document forensic analysis",
)
async def analyze_document_evidence(
    evidence_id: UUID,
    background_tasks: BackgroundTasks,
    service: DocumentAnalysisServiceDependency,
) -> ApiResponse[ProcessingJobResponse]:
    """Queue AI document analysis without modifying original evidence."""

    job = await service.create_job(evidence_id)
    background_tasks.add_task(service.run, job.id)
    return ApiResponse(data=job, request_id=get_request_id())


@router.get(
    "/evidence/{evidence_id}/document-analysis",
    response_model=ApiResponse[DocumentAnalysisRunListResponse],
    summary="List AI document analysis history",
)
async def list_document_analysis_runs(
    evidence_id: UUID,
    service: DocumentAnalysisServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[DocumentAnalysisRunListResponse]:
    """Return AI document analysis history for one evidence item."""

    return ApiResponse(
        data=await service.list_runs(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/document-findings",
    response_model=ApiResponse[DocumentAIFindingListResponse],
    summary="List AI document findings",
)
async def list_document_findings(
    evidence_id: UUID,
    service: DocumentAnalysisServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    detector: Annotated[str | None, Query()] = None,
) -> ApiResponse[DocumentAIFindingListResponse]:
    """Return persisted AI document findings for one evidence item."""

    return ApiResponse(
        data=await service.list_findings(
            evidence_id,
            limit=limit,
            offset=offset,
            detector=detector,
        ),
        request_id=get_request_id(),
    )
