"""Version-one administration endpoints for roles, permissions, and sessions."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from backend.app.auth.middleware import CurrentPrincipal, get_auth_service
from backend.app.auth.schemas import (
    PermissionResponse,
    RoleResponse,
    SessionListResponse,
)
from backend.app.auth.service import AuthService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

roles_router = APIRouter(prefix="/roles", tags=["admin"])
permissions_router = APIRouter(prefix="/permissions", tags=["admin"])
sessions_router = APIRouter(prefix="/sessions", tags=["admin"])
AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


@roles_router.get(
    "",
    response_model=ApiResponse[list[RoleResponse]],
    summary="List roles",
)
async def list_roles(
    service: AuthServiceDependency,
) -> ApiResponse[list[RoleResponse]]:
    """Return built-in and seeded roles."""

    return ApiResponse(data=await service.list_roles(), request_id=get_request_id())


@permissions_router.get(
    "",
    response_model=ApiResponse[list[PermissionResponse]],
    summary="List permissions",
)
async def list_permissions(
    service: AuthServiceDependency,
) -> ApiResponse[list[PermissionResponse]]:
    """Return the granular permission catalog."""

    return ApiResponse(
        data=await service.list_permissions(),
        request_id=get_request_id(),
    )


@sessions_router.get(
    "",
    response_model=ApiResponse[SessionListResponse],
    summary="List sessions",
)
async def list_sessions(
    principal: CurrentPrincipal,
    service: AuthServiceDependency,
    all_users: Annotated[bool, Query()] = False,
) -> ApiResponse[SessionListResponse]:
    """List the current user's sessions, or all sessions for administrators."""

    return ApiResponse(
        data=await service.list_sessions(principal, all_users=all_users),
        request_id=get_request_id(),
    )


@sessions_router.delete(
    "/{session_id}",
    response_model=ApiResponse[dict[str, bool]],
    summary="Revoke one session",
)
async def revoke_session(
    session_id: UUID,
    principal: CurrentPrincipal,
    service: AuthServiceDependency,
) -> ApiResponse[dict[str, bool]]:
    """Revoke a single session."""

    await service.revoke_session(principal, session_id)
    return ApiResponse(data={"revoked": True}, request_id=get_request_id())


@sessions_router.delete(
    "",
    response_model=ApiResponse[dict[str, bool]],
    summary="Revoke all sessions for the current user",
)
async def revoke_all_sessions(
    principal: CurrentPrincipal,
    service: AuthServiceDependency,
) -> ApiResponse[dict[str, bool]]:
    """Revoke every session belonging to the current user."""

    await service.revoke_all_sessions(principal)
    return ApiResponse(data={"revoked": True}, request_id=get_request_id())
