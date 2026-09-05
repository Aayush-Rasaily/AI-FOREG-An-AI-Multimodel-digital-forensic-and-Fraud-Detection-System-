"""Phase 9D decision support endpoints.

Uses `/decision-support` paths to avoid colliding with Phase 8B
`/cases/{id}/workflow` and Phase 8E `/investigation-workflow`.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from backend.app.api.dependencies import get_decision_support_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.decision_support.schemas import (
    DecisionCreateRequest,
    DecisionLogListResponse,
    DecisionLogResponse,
    ReviewQueueListResponse,
    TaskUpdateRequest,
    WorkflowPreviewResponse,
    WorkflowRunResponse,
    WorkflowTaskListResponse,
    WorkflowTaskResponse,
    WorkloadMetricsResponse,
)
from backend.app.decision_support.service import DecisionSupportService

router = APIRouter(tags=["decision-support"])
ServiceDependency = Annotated[
    DecisionSupportService, Depends(get_decision_support_service),
]


@router.post(
    "/cases/{case_id}/decision-support",
    response_model=ApiResponse[WorkflowRunResponse],
)
async def generate_decision_support(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[WorkflowRunResponse]:
    data = await service.generate(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/decision-support/preview",
    response_model=ApiResponse[WorkflowPreviewResponse],
)
async def preview_decision_support(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[WorkflowPreviewResponse]:
    data = await service.preview(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/decision-support/latest",
    response_model=ApiResponse[WorkflowRunResponse],
)
async def get_latest_decision_support(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[WorkflowRunResponse]:
    data = await service.get_latest(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/decision-support",
    response_model=ApiResponse[WorkflowRunResponse],
)
async def get_case_decision_support(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[WorkflowRunResponse]:
    data = await service.get_latest(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/decision-support/tasks",
    response_model=ApiResponse[WorkflowTaskListResponse],
)
async def list_decision_support_tasks(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[WorkflowTaskListResponse]:
    data = await service.list_tasks(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/decision-support/review-queue",
    response_model=ApiResponse[ReviewQueueListResponse],
)
async def list_decision_support_review_queue(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[ReviewQueueListResponse]:
    data = await service.list_review_queue(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/decision-support/metrics",
    response_model=ApiResponse[WorkloadMetricsResponse],
)
async def get_decision_support_metrics(
    case_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[WorkloadMetricsResponse]:
    data = await service.metrics(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/decision-support/decisions",
    response_model=ApiResponse[DecisionLogListResponse],
)
async def list_decision_support_decisions(
    case_id: UUID,
    service: ServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[DecisionLogListResponse]:
    data = await service.list_decisions(case_id, limit=limit, offset=offset)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/decision-support/{run_id}",
    response_model=ApiResponse[WorkflowRunResponse],
)
async def get_decision_support_run(
    run_id: UUID,
    service: ServiceDependency,
) -> ApiResponse[WorkflowRunResponse]:
    data = await service.get_run(run_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.patch(
    "/decision-support/tasks/{task_id}",
    response_model=ApiResponse[WorkflowTaskResponse],
)
async def update_decision_support_task(
    task_id: UUID,
    payload: TaskUpdateRequest,
    service: ServiceDependency,
) -> ApiResponse[WorkflowTaskResponse]:
    data = await service.update_task(task_id, payload)
    return ApiResponse(data=data, request_id=get_request_id())


@router.post(
    "/decision-support/decisions",
    response_model=ApiResponse[DecisionLogResponse],
)
async def create_decision_support_decision(
    payload: DecisionCreateRequest,
    service: ServiceDependency,
) -> ApiResponse[DecisionLogResponse]:
    data = await service.record_decision(payload)
    return ApiResponse(data=data, request_id=get_request_id())
