"""Version-one user administration endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from backend.app.auth.middleware import get_auth_service
from backend.app.auth.schemas import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from backend.app.auth.service import AuthService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(prefix="/users", tags=["users"])
AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "",
    response_model=ApiResponse[UserResponse],
    status_code=201,
    summary="Create a user",
)
async def create_user(
    payload: UserCreateRequest,
    service: AuthServiceDependency,
) -> ApiResponse[UserResponse]:
    """Create a user account and assign roles."""

    return ApiResponse(
        data=await service.create_user(
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
            email=payload.email,
            role_names=payload.role_names,
            is_active=payload.is_active,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "",
    response_model=ApiResponse[UserListResponse],
    summary="List users",
)
async def list_users(
    service: AuthServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[UserListResponse]:
    """Return a bounded page of users."""

    return ApiResponse(
        data=await service.list_users(limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="Get a user",
)
async def get_user(
    user_id: UUID,
    service: AuthServiceDependency,
) -> ApiResponse[UserResponse]:
    """Return one user by identifier."""

    return ApiResponse(
        data=await service.get_user(user_id),
        request_id=get_request_id(),
    )


@router.patch(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="Update a user",
)
async def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    service: AuthServiceDependency,
) -> ApiResponse[UserResponse]:
    """Update profile fields, activation, or role assignment."""

    return ApiResponse(
        data=await service.update_user(
            user_id,
            display_name=payload.display_name,
            email=payload.email,
            is_active=payload.is_active,
            role_names=payload.role_names,
        ),
        request_id=get_request_id(),
    )


@router.delete(
    "/{user_id}",
    response_model=ApiResponse[dict[str, bool]],
    summary="Deactivate a user",
)
async def delete_user(
    user_id: UUID,
    service: AuthServiceDependency,
) -> ApiResponse[dict[str, bool]]:
    """Deactivate a user and revoke sessions."""

    await service.delete_user(user_id)
    return ApiResponse(data={"deactivated": True}, request_id=get_request_id())
