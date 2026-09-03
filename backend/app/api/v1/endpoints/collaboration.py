"""Version-one collaboration endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_collaboration_service
from backend.app.auth.middleware import CurrentPrincipal
from backend.app.collaboration.schemas import (
    ActivityListResponse,
    CaseMemberCreateRequest,
    CaseMemberListResponse,
    CaseMemberResponse,
    CaseMemberUpdateRequest,
    CommentCreateRequest,
    CommentListResponse,
    CommentResponse,
    CommentUpdateRequest,
    EvidenceAssignmentListResponse,
    EvidenceAssignmentResponse,
    EvidenceAssignRequest,
    NotificationListResponse,
    NotificationResponse,
    NotificationUpdateRequest,
    ReviewCreateRequest,
    ReviewResponse,
    ReviewUpdateRequest,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
    WorkflowResponse,
    WorkflowUpdateRequest,
)
from backend.app.collaboration.service import CollaborationService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["collaboration"])
CollaborationServiceDependency = Annotated[
    CollaborationService, Depends(get_collaboration_service),
]


@router.post(
    "/cases/{case_id}/members",
    response_model=ApiResponse[CaseMemberResponse],
    status_code=201,
)
async def add_case_member(
    case_id: UUID,
    payload: CaseMemberCreateRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[CaseMemberResponse]:
    return ApiResponse(
        data=await service.add_member(
            case_id,
            user_id=payload.user_id,
            role=payload.role,
            principal=principal,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/members",
    response_model=ApiResponse[CaseMemberListResponse],
)
async def list_case_members(
    case_id: UUID,
    service: CollaborationServiceDependency,
) -> ApiResponse[CaseMemberListResponse]:
    return ApiResponse(
        data=await service.list_members(case_id),
        request_id=get_request_id(),
    )


@router.patch(
    "/cases/{case_id}/members/{member_id}",
    response_model=ApiResponse[CaseMemberResponse],
)
async def update_case_member(
    case_id: UUID,
    member_id: UUID,
    payload: CaseMemberUpdateRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[CaseMemberResponse]:
    return ApiResponse(
        data=await service.update_member(
            case_id,
            member_id,
            role=payload.role,
            transfer_ownership=payload.transfer_ownership,
            principal=principal,
        ),
        request_id=get_request_id(),
    )


@router.delete(
    "/cases/{case_id}/members/{member_id}",
    response_model=ApiResponse[dict[str, bool]],
)
async def remove_case_member(
    case_id: UUID,
    member_id: UUID,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[dict[str, bool]]:
    await service.remove_member(case_id, member_id, principal)
    return ApiResponse(data={"removed": True}, request_id=get_request_id())


@router.post(
    "/cases/{case_id}/tasks",
    response_model=ApiResponse[TaskResponse],
    status_code=201,
)
async def create_case_task(
    case_id: UUID,
    payload: TaskCreateRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[TaskResponse]:
    return ApiResponse(
        data=await service.create_task(
            case_id,
            title=payload.title,
            description=payload.description,
            assignee_id=payload.assignee_id,
            priority=payload.priority,
            due_date=payload.due_date,
            linked_evidence_id=payload.linked_evidence_id,
            linked_report_id=payload.linked_report_id,
            principal=principal,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/tasks",
    response_model=ApiResponse[TaskListResponse],
)
async def list_case_tasks(
    case_id: UUID,
    service: CollaborationServiceDependency,
) -> ApiResponse[TaskListResponse]:
    return ApiResponse(
        data=await service.list_tasks(case_id),
        request_id=get_request_id(),
    )


@router.patch(
    "/tasks/{task_id}",
    response_model=ApiResponse[TaskResponse],
)
async def update_task(
    task_id: UUID,
    payload: TaskUpdateRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[TaskResponse]:
    updates = payload.model_dump(exclude_unset=True)
    return ApiResponse(
        data=await service.update_task(
            task_id, updates=updates, principal=principal,
        ),
        request_id=get_request_id(),
    )


@router.delete(
    "/tasks/{task_id}",
    response_model=ApiResponse[dict[str, bool]],
)
async def delete_task(
    task_id: UUID,
    service: CollaborationServiceDependency,
) -> ApiResponse[dict[str, bool]]:
    await service.delete_task(task_id)
    return ApiResponse(data={"deleted": True}, request_id=get_request_id())


@router.post(
    "/evidence/{evidence_id}/assign",
    response_model=ApiResponse[EvidenceAssignmentResponse],
    status_code=201,
)
async def assign_evidence(
    evidence_id: UUID,
    payload: EvidenceAssignRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[EvidenceAssignmentResponse]:
    return ApiResponse(
        data=await service.assign_evidence(
            evidence_id,
            assignee_id=payload.assignee_id,
            priority=payload.priority,
            due_date=payload.due_date,
            notes=payload.notes,
            principal=principal,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/assignments",
    response_model=ApiResponse[EvidenceAssignmentListResponse],
)
async def list_evidence_assignments(
    evidence_id: UUID,
    service: CollaborationServiceDependency,
) -> ApiResponse[EvidenceAssignmentListResponse]:
    return ApiResponse(
        data=await service.list_assignments(evidence_id),
        request_id=get_request_id(),
    )


@router.post(
    "/comments",
    response_model=ApiResponse[CommentResponse],
    status_code=201,
)
async def create_comment(
    payload: CommentCreateRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[CommentResponse]:
    return ApiResponse(
        data=await service.create_comment(
            case_id=payload.case_id,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            body=payload.body,
            parent_id=payload.parent_id,
            body_markdown=payload.body_markdown,
            principal=principal,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/comments/{resource_type}/{resource_id}",
    response_model=ApiResponse[CommentListResponse],
)
async def list_comments(
    resource_type: str,
    resource_id: str,
    service: CollaborationServiceDependency,
) -> ApiResponse[CommentListResponse]:
    return ApiResponse(
        data=await service.list_comments(resource_type, resource_id),
        request_id=get_request_id(),
    )


@router.patch(
    "/comments/{comment_id}",
    response_model=ApiResponse[CommentResponse],
)
async def update_comment(
    comment_id: UUID,
    payload: CommentUpdateRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[CommentResponse]:
    return ApiResponse(
        data=await service.update_comment(
            comment_id, body=payload.body, principal=principal,
        ),
        request_id=get_request_id(),
    )


@router.delete(
    "/comments/{comment_id}",
    response_model=ApiResponse[CommentResponse],
)
async def delete_comment(
    comment_id: UUID,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[CommentResponse]:
    return ApiResponse(
        data=await service.delete_comment(comment_id, principal),
        request_id=get_request_id(),
    )


@router.post(
    "/reviews",
    response_model=ApiResponse[ReviewResponse],
    status_code=201,
)
async def create_review(
    payload: ReviewCreateRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[ReviewResponse]:
    return ApiResponse(
        data=await service.create_review(
            case_id=payload.case_id,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            reviewer_id=payload.reviewer_id,
            comments=payload.comments,
            principal=principal,
        ),
        request_id=get_request_id(),
    )


@router.patch(
    "/reviews/{review_id}",
    response_model=ApiResponse[ReviewResponse],
)
async def update_review(
    review_id: UUID,
    payload: ReviewUpdateRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[ReviewResponse]:
    return ApiResponse(
        data=await service.update_review(
            review_id,
            decision=payload.decision,
            comments=payload.comments,
            reviewer_id=payload.reviewer_id,
            principal=principal,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/notifications",
    response_model=ApiResponse[NotificationListResponse],
)
async def list_notifications(
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[NotificationListResponse]:
    return ApiResponse(
        data=await service.list_notifications(principal),
        request_id=get_request_id(),
    )


@router.patch(
    "/notifications/{notification_id}",
    response_model=ApiResponse[NotificationResponse],
)
async def update_notification(
    notification_id: UUID,
    payload: NotificationUpdateRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[NotificationResponse]:
    return ApiResponse(
        data=await service.update_notification(
            notification_id, status=payload.status, principal=principal,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/activity",
    response_model=ApiResponse[ActivityListResponse],
)
async def list_case_activity(
    case_id: UUID,
    service: CollaborationServiceDependency,
) -> ApiResponse[ActivityListResponse]:
    return ApiResponse(
        data=await service.list_activity(case_id),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/workflow",
    response_model=ApiResponse[WorkflowResponse],
)
async def get_case_workflow(
    case_id: UUID,
    service: CollaborationServiceDependency,
) -> ApiResponse[WorkflowResponse]:
    return ApiResponse(
        data=await service.get_workflow(case_id),
        request_id=get_request_id(),
    )


@router.patch(
    "/cases/{case_id}/workflow",
    response_model=ApiResponse[WorkflowResponse],
)
async def update_case_workflow(
    case_id: UUID,
    payload: WorkflowUpdateRequest,
    service: CollaborationServiceDependency,
    principal: CurrentPrincipal,
) -> ApiResponse[WorkflowResponse]:
    return ApiResponse(
        data=await service.transition_workflow(
            case_id, stage=payload.stage, principal=principal,
        ),
        request_id=get_request_id(),
    )
