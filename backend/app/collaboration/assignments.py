"""Evidence assignment helpers."""

from __future__ import annotations

from backend.app.collaboration.exceptions import CollaborationError
from backend.app.collaboration.policy import AssignmentStatus


def normalize_assignment_status(status: str) -> str:
    """Validate and return an assignment status value."""

    try:
        return AssignmentStatus(status).value
    except ValueError as exc:
        raise CollaborationError(f"Unknown assignment status: {status}") from exc
