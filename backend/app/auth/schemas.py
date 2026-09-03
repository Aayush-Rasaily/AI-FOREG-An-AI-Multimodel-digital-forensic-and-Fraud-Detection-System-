"""Pydantic schemas for authentication and user administration."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Username and password login payload."""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
    remember_me: bool = False


class TokenResponse(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshRequest(BaseModel):
    """Refresh token exchange payload."""

    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    """Optional refresh token to revoke on logout."""

    refresh_token: str | None = None


class PasswordChangeRequest(BaseModel):
    """Authenticated password change payload."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class UserCreateRequest(BaseModel):
    """Administrator user creation payload."""

    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)
    email: str | None = Field(default=None, max_length=256)
    role_names: list[str] = Field(default_factory=list)
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    """Partial user update payload."""

    display_name: str | None = Field(default=None, max_length=128)
    email: str | None = Field(default=None, max_length=256)
    is_active: bool | None = None
    role_names: list[str] | None = None


class RoleResponse(BaseModel):
    """Public role record."""

    id: UUID
    name: str
    description: str
    is_system: bool
    permissions: list[str]


class PermissionResponse(BaseModel):
    """Public permission record."""

    code: str
    description: str


class UserResponse(BaseModel):
    """Public user record."""

    id: UUID
    username: str
    display_name: str
    email: str | None
    is_active: bool
    is_locked: bool
    roles: list[str]
    permissions: list[str]
    last_login_at: datetime | None
    created_at: datetime


class UserListResponse(BaseModel):
    """Paged user list."""

    items: list[UserResponse]
    total: int
    limit: int
    offset: int


class SessionResponse(BaseModel):
    """Public session record."""

    id: UUID
    user_id: UUID
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    device_name: str | None
    browser: str | None
    ip_address: str | None
    remember_me: bool
    revoked: bool
    current: bool = False


class SessionListResponse(BaseModel):
    """Session list for the current user or administrator."""

    items: list[SessionResponse]
    total: int
