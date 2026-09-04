"""Phase 8F security, compliance, and governance endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from backend.app.api.dependencies import get_security_service
from backend.app.auth.models import AuthenticatedPrincipal
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.security.schemas import (
    CaseAccessListResponse,
    CaseAccessResponse,
    CaseAccessUpdateRequest,
    ComplianceResponse,
    PolicyDocumentResponse,
    PolicyViolationListResponse,
    SecurityPermissionListResponse,
    SecurityRoleListResponse,
    ValidationRequest,
    ValidationResponse,
)
from backend.app.security.service import SecurityService

router = APIRouter(tags=["security-governance"])
SecurityServiceDependency = Annotated[
    SecurityService, Depends(get_security_service),
]


def _principal(request: Request) -> AuthenticatedPrincipal | None:
    existing = getattr(request.state, "principal", None)
    if isinstance(existing, AuthenticatedPrincipal):
        return existing
    return None


@router.get(
    "/security/roles",
    response_model=ApiResponse[SecurityRoleListResponse],
)
async def list_security_roles(
    service: SecurityServiceDependency,
) -> ApiResponse[SecurityRoleListResponse]:
    return ApiResponse(
        data=await service.list_roles(),
        request_id=get_request_id(),
    )


@router.get(
    "/security/permissions",
    response_model=ApiResponse[SecurityPermissionListResponse],
)
async def list_security_permissions(
    service: SecurityServiceDependency,
) -> ApiResponse[SecurityPermissionListResponse]:
    return ApiResponse(
        data=await service.list_permissions(),
        request_id=get_request_id(),
    )


@router.get(
    "/security/policy",
    response_model=ApiResponse[PolicyDocumentResponse],
)
async def get_security_policy(
    service: SecurityServiceDependency,
) -> ApiResponse[PolicyDocumentResponse]:
    return ApiResponse(
        data=await service.get_policy(),
        request_id=get_request_id(),
    )


@router.get(
    "/security/violations",
    response_model=ApiResponse[PolicyViolationListResponse],
)
async def list_security_violations(
    service: SecurityServiceDependency,
    case_id: UUID | None = None,
) -> ApiResponse[PolicyViolationListResponse]:
    return ApiResponse(
        data=await service.list_violations(case_id=case_id),
        request_id=get_request_id(),
    )


@router.post(
    "/security/validate",
    response_model=ApiResponse[ValidationResponse],
)
async def validate_security_chain(
    payload: ValidationRequest,
    request: Request,
    service: SecurityServiceDependency,
) -> ApiResponse[ValidationResponse]:
    return ApiResponse(
        data=await service.validate(
            case_id=payload.case_id,
            principal=_principal(request),
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/access",
    response_model=ApiResponse[CaseAccessListResponse],
)
async def list_case_access(
    case_id: UUID,
    request: Request,
    service: SecurityServiceDependency,
) -> ApiResponse[CaseAccessListResponse]:
    return ApiResponse(
        data=await service.list_case_access(case_id, _principal(request)),
        request_id=get_request_id(),
    )


@router.patch(
    "/cases/{case_id}/access",
    response_model=ApiResponse[CaseAccessResponse],
)
async def patch_case_access(
    case_id: UUID,
    payload: CaseAccessUpdateRequest,
    request: Request,
    service: SecurityServiceDependency,
) -> ApiResponse[CaseAccessResponse]:
    return ApiResponse(
        data=await service.update_case_access(
            case_id,
            user_id=payload.user_id,
            access_level=payload.access_level,
            reason=payload.reason,
            active=payload.active,
            principal=_principal(request),
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/compliance",
    response_model=ApiResponse[ComplianceResponse],
)
async def get_case_compliance(
    case_id: UUID,
    request: Request,
    service: SecurityServiceDependency,
) -> ApiResponse[ComplianceResponse]:
    return ApiResponse(
        data=await service.get_case_compliance(case_id, _principal(request)),
        request_id=get_request_id(),
    )
