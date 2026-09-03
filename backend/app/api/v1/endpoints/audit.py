"""Version-one audit trail endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from backend.app.api.dependencies import get_audit_service
from backend.app.audit.schemas import (
    AuditEventListResponse,
    AuditEventResponse,
    IntegrityVerifyResponse,
)
from backend.app.audit.service import AuditService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["audit"])
AuditServiceDependency = Annotated[
    AuditService, Depends(get_audit_service),
]


@router.get(
    "/audit",
    response_model=ApiResponse[AuditEventListResponse],
    summary="List audit events",
)
async def list_audit_events(
    service: AuditServiceDependency,
    operation: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[AuditEventListResponse]:
    """Return paginated audit events with optional filters."""
    return ApiResponse(
        data=await service.list_events(
            operation=operation,
            category=category,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.post(
    "/audit/verify",
    response_model=ApiResponse[IntegrityVerifyResponse],
    summary="Verify evidence and report integrity",
)
async def verify_integrity(
    service: AuditServiceDependency,
    case_id: Annotated[UUID | None, Query()] = None,
    evidence_id: Annotated[UUID | None, Query()] = None,
    report_id: Annotated[UUID | None, Query()] = None,
) -> ApiResponse[IntegrityVerifyResponse]:
    """Verify integrity checksums."""
    return ApiResponse(
        data=await service.verify_integrity(
            case_id=case_id,
            evidence_id=evidence_id,
            report_id=report_id,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/audit/export",
    summary="Export audit log",
)
async def export_audit_log(
    service: AuditServiceDependency,
    case_id: Annotated[UUID | None, Query()] = None,
) -> Response:
    """Export the audit log as JSON."""
    result = await service.export_audit_log(case_id=case_id)
    return Response(
        content=result.payload,
        media_type="application/json",
        headers={
            "Content-Disposition": (
                'attachment; filename="audit-log.json"'
            ),
            "X-Audit-Checksum": result.checksum,
        },
    )


@router.get(
    "/audit/{event_id}",
    response_model=ApiResponse[AuditEventResponse],
    summary="Get one audit event",
)
async def get_audit_event(
    event_id: UUID,
    service: AuditServiceDependency,
) -> ApiResponse[AuditEventResponse]:
    """Return a single audit event."""
    return ApiResponse(
        data=await service.get_event(event_id),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/audit",
    response_model=ApiResponse[AuditEventListResponse],
    summary="List audit events for a case",
)
async def list_case_audit_events(
    case_id: UUID,
    service: AuditServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[AuditEventListResponse]:
    """Return audit events scoped to one case."""
    return ApiResponse(
        data=await service.list_events(
            case_id=case_id, limit=limit, offset=offset,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}/audit",
    response_model=ApiResponse[AuditEventListResponse],
    summary="List audit events for evidence",
)
async def list_evidence_audit_events(
    evidence_id: UUID,
    service: AuditServiceDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[AuditEventListResponse]:
    """Return audit events scoped to one evidence item."""
    return ApiResponse(
        data=await service.list_events(
            evidence_id=evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )
