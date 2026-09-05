"""Phase 9E case review endpoints.

Uses `/case-review` paths to avoid colliding with Phase 8B `/reviews`
and Phase 8E `/workflow-reviews`.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from backend.app.api.dependencies import get_case_review_service
from backend.app.case_review.schemas import (
    ApprovalCreateRequest,
    ApprovalListResponse,
    ApprovalResponse,
    CaseReviewHistoryResponse,
    CaseReviewPreviewResponse,
    CaseReviewRunResponse,
    ChecklistItemResponse,
    ChecklistItemUpdateRequest,
    ChecklistListResponse,
    ValidationMetricsResponse,
)
from backend.app.case_review.service import CaseReviewService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["case-review"])
ServiceDependency = Annotated[
    CaseReviewService,
    Depends(get_case_review_service),
]


@router.post(
    "/cases/{case_id}/case-review",
    response_model=ApiResponse[CaseReviewRunResponse],
)
async def generate_case_review(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[CaseReviewRunResponse]:
    data = await service.generate(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/case-review/preview",
    response_model=ApiResponse[CaseReviewPreviewResponse],
)
async def preview_case_review(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[CaseReviewPreviewResponse]:
    data = await service.preview(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/case-review/latest",
    response_model=ApiResponse[CaseReviewRunResponse],
)
async def get_latest_case_review(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[CaseReviewRunResponse]:
    data = await service.get_latest(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/case-review",
    response_model=ApiResponse[CaseReviewRunResponse],
)
async def get_case_review(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[CaseReviewRunResponse]:
    data = await service.get_latest(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/case-review/checklist",
    response_model=ApiResponse[ChecklistListResponse],
)
async def list_case_review_checklist(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[ChecklistListResponse]:
    data = await service.list_checklist(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/case-review/approvals",
    response_model=ApiResponse[ApprovalListResponse],
)
async def list_case_review_approvals(
    case_id: UUID,
    service: ServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[ApprovalListResponse]:
    data = await service.list_approvals(case_id, limit=limit, offset=offset)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/case-review/metrics",
    response_model=ApiResponse[ValidationMetricsResponse],
)
async def get_case_review_metrics(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[ValidationMetricsResponse]:
    data = await service.metrics(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/case-review/history",
    response_model=ApiResponse[CaseReviewHistoryResponse],
)
async def get_case_review_history(
    case_id: UUID,
    service: ServiceDependency,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[CaseReviewHistoryResponse]:
    data = await service.history(case_id, limit=limit, offset=offset)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/case-review/{review_id}",
    response_model=ApiResponse[CaseReviewRunResponse],
)
async def get_case_review_run(
    review_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[CaseReviewRunResponse]:
    data = await service.get_run(review_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.patch(
    "/case-review/checklist/{item_id}",
    response_model=ApiResponse[ChecklistItemResponse],
)
async def update_case_review_checklist_item(
    item_id: UUID,
    payload: ChecklistItemUpdateRequest,
    service: ServiceDependency,
) -> ApiResponse[ChecklistItemResponse]:
    data = await service.update_checklist_item(item_id, payload)
    return ApiResponse(data=data, request_id=get_request_id())


@router.post(
    "/case-review/approvals",
    response_model=ApiResponse[ApprovalResponse],
)
async def create_case_review_approval(
    payload: ApprovalCreateRequest,
    service: ServiceDependency,
) -> ApiResponse[ApprovalResponse]:
    data = await service.record_approval(payload)
    return ApiResponse(data=data, request_id=get_request_id())
