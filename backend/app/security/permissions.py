"""Fine-grained governance permission helpers."""

from __future__ import annotations

from backend.app.security.policy import (
    GOVERNANCE_PERMISSION_MATRIX,
    PERMISSION_CATALOG,
    GovernanceRole,
)


def all_permission_codes() -> list[str]:
    """Return sorted catalog permission codes."""

    return sorted(item[0] for item in PERMISSION_CATALOG)


def permissions_for_role(role: str) -> list[str]:
    """Return sorted permission codes granted to a governance role."""

    try:
        gov = GovernanceRole(role)
    except ValueError:
        return []
    return sorted(GOVERNANCE_PERMISSION_MATRIX[gov])


def role_has_permission(role: str, permission: str) -> bool:
    """Return whether a governance role includes a permission."""

    return permission in set(permissions_for_role(role))


def roles_with_permission(permission: str) -> list[str]:
    """Return governance roles that include the permission."""

    return sorted(
        role.value
        for role, codes in GOVERNANCE_PERMISSION_MATRIX.items()
        if permission in codes
    )
