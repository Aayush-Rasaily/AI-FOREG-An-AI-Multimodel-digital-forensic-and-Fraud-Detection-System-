"""Version-one authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from backend.app.auth.middleware import CurrentPrincipal, get_auth_service
from backend.app.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    PasswordChangeRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from backend.app.auth.security import client_ip
from backend.app.auth.service import AuthService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(prefix="/auth", tags=["auth"])
AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Sign in with username and password",
)
async def login(
    payload: LoginRequest,
    request: Request,
    service: AuthServiceDependency,
) -> ApiResponse[TokenResponse]:
    """Issue access and refresh tokens for a valid account."""

    tokens = await service.login(
        username=payload.username,
        password=payload.password,
        remember_me=payload.remember_me,
        ip_address=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return ApiResponse(data=tokens, request_id=get_request_id())


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="Refresh an access token",
)
async def refresh(
    payload: RefreshRequest,
    service: AuthServiceDependency,
) -> ApiResponse[TokenResponse]:
    """Rotate tokens using a valid refresh token."""

    return ApiResponse(
        data=await service.refresh(payload.refresh_token),
        request_id=get_request_id(),
    )


@router.post(
    "/logout",
    response_model=ApiResponse[dict[str, bool]],
    summary="Sign out of the current session",
)
async def logout(
    principal: CurrentPrincipal,
    service: AuthServiceDependency,
    payload: LogoutRequest | None = None,
) -> ApiResponse[dict[str, bool]]:
    """Revoke the current session."""

    await service.logout(
        principal,
        refresh_token=payload.refresh_token if payload else None,
    )
    return ApiResponse(data={"revoked": True}, request_id=get_request_id())


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Get the current user",
)
async def read_me(
    principal: CurrentPrincipal,
    service: AuthServiceDependency,
) -> ApiResponse[UserResponse]:
    """Return the authenticated user profile."""

    return ApiResponse(data=await service.me(principal), request_id=get_request_id())


@router.post(
    "/password",
    response_model=ApiResponse[dict[str, bool]],
    summary="Change the current password",
)
async def change_password(
    payload: PasswordChangeRequest,
    principal: CurrentPrincipal,
    service: AuthServiceDependency,
) -> ApiResponse[dict[str, bool]]:
    """Replace the current password and revoke other sessions."""

    await service.change_password(
        principal,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return ApiResponse(data={"updated": True}, request_id=get_request_id())
