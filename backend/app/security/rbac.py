"""Deterministic RBAC matrix for enterprise governance roles."""

from __future__ import annotations

from typing import Any

from backend.app.security.permissions import (
    all_permission_codes,
    permissions_for_role,
)
from backend.app.security.policy import (
    GOVERNANCE_PERMISSION_MATRIX,
    PERMISSION_CATALOG,
    ROLE_DESCRIPTIONS,
    SECURITY_POLICY_VERSION,
    GovernanceRole,
)


def build_role_catalog() -> list[dict[str, Any]]:
    """Return the deterministic governance role catalog."""

    items: list[dict[str, Any]] = []
    for role in GovernanceRole:
        items.append(
            {
                "code": role.value,
                "name": role.value.replace("_", " ").title(),
                "description": ROLE_DESCRIPTIONS[role],
                "permissions": permissions_for_role(role.value),
                "policy_version": SECURITY_POLICY_VERSION,
            }
        )
    return items


def build_permission_catalog() -> list[dict[str, Any]]:
    """Return the deterministic permission catalog."""

    items = [
        {
            "code": code,
            "resource": resource,
            "action": action,
            "description": description,
            "roles": [
                role.value
                for role, codes in GOVERNANCE_PERMISSION_MATRIX.items()
                if code in codes
            ],
            "policy_version": SECURITY_POLICY_VERSION,
        }
        for code, resource, action, description in PERMISSION_CATALOG
    ]
    return sorted(items, key=lambda item: item["code"])


def assert_permission_known(permission: str) -> None:
    """Raise ValueError when permission is outside the catalog."""

    if permission not in set(all_permission_codes()):
        raise ValueError(f"Unknown permission: {permission}")
