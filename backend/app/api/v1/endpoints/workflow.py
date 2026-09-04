"""Phase 8E investigation workflow endpoints.

Paths are namespaced (`investigation-workflow`, `workflow-*`) because
Phase 8B collaboration already owns `/cases/{id}/workflow`, `/tasks`,
`/reviews`, and `/notifications`. Functional coverage matches the Phase 8E
specification.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from backend.app.api.dependencies import get_workflow_service
from backend.app.auth.models import AuthenticatedPrincipal
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.workflow.schemas import (
    MilestoneListResponse,
    NoteCreateRequest,
    NoteListResponse,
    NoteResponse,
    NotificationListResponse,
    ReviewCreateRequest,
    ReviewListResponse,
    ReviewResponse,
    ReviewUpdateRequest,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
    WorkflowResponse,
    WorkflowStatusUpdateRequest,
)
from backend.app.workflow.service import WorkflowService

router = APIRouter(tags=["investigation-workflow"])
WorkflowServiceDependency = Annotated[
    WorkflowService, Depends(get_workflow_service),
]


def _principal(request: Request) -> AuthenticatedPrincipal | None:
    existing = getattr(request.state, "principal", None)
    if isinstance(existing, AuthenticatedPrincipal):
        return existing
    return None


@router.get(
    "/cases/{case_id}/investigation-workflow",
    response_model=ApiResponse[WorkflowResponse],
)
async def get_investigation_workflow(
    case_id: UUID,
    request: Request,
    service: WorkflowServiceDependency,
) -> ApiResponse[WorkflowResponse]:
    return ApiResponse(
        data=await service.get_workflow(case_id, _principal(request)),
        request_id=get_request_id(),
    )


@router.patch(
    "/cases/{case_id}/investigation-workflow/status",
    response_model=ApiResponse[WorkflowResponse],
)
async def patch_investigation_workflow_status(
    case_id: UUID,
    payload: WorkflowStatusUpdateRequest,
    request: Request,
    service: WorkflowServiceDependency,
) -> ApiResponse[WorkflowResponse]:
    return ApiResponse(
        data=await service.update_status(
            case_id,
            status=payload.status,
            assigned_analyst_id=payload.assigned_analyst_id,
            principal=_principal(request),
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/workflow-tasks",
    response_model=ApiResponse[TaskListResponse],
)
async def list_workflow_tasks(
    case_id: UUID,
    service: WorkflowServiceDependency,
) -> ApiResponse[TaskListResponse]:
    return ApiResponse(
        data=await service.list_tasks(case_id),
        request_id=get_request_id(),
    )


@router.post(
    "/cases/{case_id}/workflow-tasks",
    response_model=ApiResponse[TaskResponse],
    status_code=201,
)
async def create_workflow_task(
    case_id: UUID,
    payload: TaskCreateRequest,
    request: Request,
    service: WorkflowServiceDependency,
) -> ApiResponse[TaskResponse]:
    return ApiResponse(
        data=await service.create_task(
            case_id,
            title=payload.title,
            task_type=payload.task_type,
            description=payload.description,
            assignee_id=payload.assignee_id,
            linked_evidence_id=payload.linked_evidence_id,
            linked_report_id=payload.linked_report_id,
            principal=_principal(request),
        ),
        request_id=get_request_id(),
    )


@router.patch(
    "/workflow-tasks/{task_id}",
    response_model=ApiResponse[TaskResponse],
)
async def patch_workflow_task(
    task_id: UUID,
    payload: TaskUpdateRequest,
    request: Request,
    service: WorkflowServiceDependency,
) -> ApiResponse[TaskResponse]:
    return ApiResponse(
        data=await service.update_task(
            task_id,
            title=payload.title,
            description=payload.description,
            assignee_id=payload.assignee_id,
            status=payload.status,
            action=payload.action,
            principal=_principal(request),
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/workflow-notes",
    response_model=ApiResponse[NoteListResponse],
)
async def list_workflow_notes(
    case_id: UUID,
    service: WorkflowServiceDependency,
) -> ApiResponse[NoteListResponse]:
    return ApiResponse(
        data=await service.list_notes(case_id),
        request_id=get_request_id(),
    )


@router.post(
    "/cases/{case_id}/workflow-notes",
    response_model=ApiResponse[NoteResponse],
    status_code=201,
)
async def create_workflow_note(
    case_id: UUID,
    payload: NoteCreateRequest,
    request: Request,
    service: WorkflowServiceDependency,
) -> ApiResponse[NoteResponse]:
    return ApiResponse(
        data=await service.create_note(
            case_id,
            content_markdown=payload.content_markdown,
            category=payload.category,
            visibility=payload.visibility,
            principal=_principal(request),
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/workflow-reviews",
    response_model=ApiResponse[ReviewListResponse],
)
async def list_workflow_reviews(
    case_id: UUID,
    service: WorkflowServiceDependency,
) -> ApiResponse[ReviewListResponse]:
    return ApiResponse(
        data=await service.list_reviews(case_id),
        request_id=get_request_id(),
    )


@router.post(
    "/cases/{case_id}/workflow-reviews",
    response_model=ApiResponse[ReviewResponse],
    status_code=201,
)
async def create_workflow_review(
    case_id: UUID,
    payload: ReviewCreateRequest,
    request: Request,
    service: WorkflowServiceDependency,
) -> ApiResponse[ReviewResponse]:
    return ApiResponse(
        data=await service.create_review(
            case_id,
            review_kind=payload.review_kind,
            status=payload.status,
            evidence_id=payload.evidence_id,
            report_id=payload.report_id,
            reviewer_id=payload.reviewer_id,
            comments=payload.comments,
            reason=payload.reason,
            principal=_principal(request),
        ),
        request_id=get_request_id(),
    )


@router.patch(
    "/workflow-reviews/{review_id}",
    response_model=ApiResponse[ReviewResponse],
)
async def patch_workflow_review(
    review_id: UUID,
    payload: ReviewUpdateRequest,
    request: Request,
    service: WorkflowServiceDependency,
) -> ApiResponse[ReviewResponse]:
    return ApiResponse(
        data=await service.transition_review(
            review_id,
            status=payload.status,
            comments=payload.comments,
            reason=payload.reason,
            principal=_principal(request),
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/workflow-milestones",
    response_model=ApiResponse[MilestoneListResponse],
)
async def list_workflow_milestones(
    case_id: UUID,
    request: Request,
    service: WorkflowServiceDependency,
) -> ApiResponse[MilestoneListResponse]:
    return ApiResponse(
        data=await service.list_milestones(case_id, _principal(request)),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/workflow-notifications",
    response_model=ApiResponse[NotificationListResponse],
)
async def list_workflow_notifications(
    case_id: UUID,
    service: WorkflowServiceDependency,
) -> ApiResponse[NotificationListResponse]:
    return ApiResponse(
        data=await service.list_notifications(case_id),
        request_id=get_request_id(),
    )
