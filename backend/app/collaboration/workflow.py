"""Case workflow stage transitions."""

from __future__ import annotations

from backend.app.collaboration.exceptions import InvalidWorkflowTransitionError
from backend.app.collaboration.policy import (
    ALLOWED_WORKFLOW_TRANSITIONS,
    CaseWorkflowStage,
)


def allowed_transitions(stage: str) -> list[str]:
    """Return allowed next stages for the current stage."""

    current = CaseWorkflowStage(stage)
    return sorted(item.value for item in ALLOWED_WORKFLOW_TRANSITIONS[current])


def assert_transition(current: str, target: str) -> CaseWorkflowStage:
    """Validate a workflow transition and return the target stage."""

    try:
        current_stage = CaseWorkflowStage(current)
        target_stage = CaseWorkflowStage(target)
    except ValueError as exc:
        raise InvalidWorkflowTransitionError(
            f"Unknown workflow stage: {target}"
        ) from exc
    allowed = ALLOWED_WORKFLOW_TRANSITIONS[current_stage]
    if target_stage not in allowed:
        raise InvalidWorkflowTransitionError(
            f"Cannot transition from {current} to {target}."
        )
    return target_stage
