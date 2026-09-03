"""Authentication domain models."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    """Resolved identity for one authenticated request."""

    user_id: UUID
    username: str
    display_name: str
    email: str | None
    roles: tuple[str, ...]
    permissions: frozenset[str]
    session_id: UUID
    is_active: bool

    def has_permission(self, permission: str) -> bool:
        """Return True when the principal holds the named permission."""

        return permission in self.permissions
