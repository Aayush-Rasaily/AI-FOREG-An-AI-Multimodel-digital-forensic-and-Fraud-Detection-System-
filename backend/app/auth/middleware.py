"""Request authentication and permission enforcement."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from backend.app.api.dependencies import SessionDependency, get_runtime_settings
from backend.app.auth.exceptions import AuthenticationError, AuthorizationError
from backend.app.auth.models import AuthenticatedPrincipal
from backend.app.auth.permissions import (
    is_public_path,
    required_permission,
    strip_api_prefix,
)
from backend.app.auth.security import extract_bearer_token
from backend.app.auth.service import AuthService
from backend.app.core.config import Settings


def get_auth_service(
    session: SessionDependency,
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> AuthService:
    """Compose the authentication service for one request."""

    return AuthService(session=session, settings=settings)


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


async def require_request_authorization(
    request: Request,
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    service: AuthServiceDependency,
) -> AuthenticatedPrincipal | None:
    """Authenticate and authorize the current request when auth is enabled."""

    if not settings.auth_required:
        return None
    path = strip_api_prefix(request.url.path, settings.api_prefix)
    method = request.method.upper()
    if method == "OPTIONS" or is_public_path(method, path):
        return None
    token = extract_bearer_token(request)
    if token is None:
        raise AuthenticationError("Authentication is required.")
    principal = await service.resolve_access_token(token)
    request.state.principal = principal
    permission = required_permission(method, path)
    if permission and not principal.has_permission(permission):
        raise AuthorizationError("You do not have permission to perform this action.")
    return principal


async def get_current_principal(
    request: Request,
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    service: AuthServiceDependency,
) -> AuthenticatedPrincipal:
    """Require an authenticated principal for identity-scoped endpoints."""

    existing = getattr(request.state, "principal", None)
    if isinstance(existing, AuthenticatedPrincipal):
        return existing
    if not settings.auth_required:
        raise AuthenticationError("Authentication is not configured.")
    token = extract_bearer_token(request)
    if token is None:
        raise AuthenticationError("Authentication is required.")
    principal = await service.resolve_access_token(token)
    request.state.principal = principal
    return principal


CurrentPrincipal = Annotated[
    AuthenticatedPrincipal, Depends(get_current_principal),
]
