"""Phase 9C investigation intelligence endpoints.

Uses `/investigation-intelligence` paths to avoid colliding with Phase 8C
`/investigation-summaries` and Phase 6G `/intelligence`.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from backend.app.api.dependencies import get_investigation_intelligence_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.investigation_intelligence.schemas import (
    EvidenceGapListResponse,
    HypothesisListResponse,
    IntelligencePreviewResponse,
    IntelligenceRunResponse,
    InvestigationSummaryResponse,
    RecommendationListResponse,
)
from backend.app.investigation_intelligence.service import (
    InvestigationIntelligenceEngineService,
)

router = APIRouter(tags=["case-investigation-intelligence"])
ServiceDependency = Annotated[
    InvestigationIntelligenceEngineService,
    Depends(get_investigation_intelligence_service),
]


@router.post(
    "/cases/{case_id}/investigation-intelligence",
    response_model=ApiResponse[IntelligenceRunResponse],
)
async def analyze_investigation_intelligence(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntelligenceRunResponse]:
    data = await service.analyze(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/investigation-preview",
    response_model=ApiResponse[IntelligencePreviewResponse],
)
async def preview_investigation_intelligence(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntelligencePreviewResponse]:
    data = await service.preview(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/investigation-intelligence/latest",
    response_model=ApiResponse[IntelligenceRunResponse],
)
async def get_latest_investigation_intelligence(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntelligenceRunResponse]:
    data = await service.get_latest(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/investigation-intelligence",
    response_model=ApiResponse[IntelligenceRunResponse],
)
async def get_case_investigation_intelligence(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntelligenceRunResponse]:
    data = await service.get_latest(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/hypotheses",
    response_model=ApiResponse[HypothesisListResponse],
)
async def list_hypotheses(
    case_id: UUID,
    service: ServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[HypothesisListResponse]:
    data = await service.list_hypotheses(case_id, limit=limit, offset=offset)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/evidence-gaps",
    response_model=ApiResponse[EvidenceGapListResponse],
)
async def list_evidence_gaps(
    case_id: UUID,
    service: ServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[EvidenceGapListResponse]:
    data = await service.list_gaps(case_id, limit=limit, offset=offset)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/recommendations",
    response_model=ApiResponse[RecommendationListResponse],
)
async def list_recommendations(
    case_id: UUID,
    service: ServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[RecommendationListResponse]:
    data = await service.list_recommendations(
        case_id, limit=limit, offset=offset,
    )
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/investigation-summary",
    response_model=ApiResponse[InvestigationSummaryResponse],
)
async def get_investigation_summary(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[InvestigationSummaryResponse]:
    data = await service.investigation_summary(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/investigation-intelligence/{run_id}",
    response_model=ApiResponse[IntelligenceRunResponse],
)
async def get_investigation_intelligence_run(
    run_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[IntelligenceRunResponse]:
    data = await service.get_run(run_id)
    return ApiResponse(data=data, request_id=get_request_id())
