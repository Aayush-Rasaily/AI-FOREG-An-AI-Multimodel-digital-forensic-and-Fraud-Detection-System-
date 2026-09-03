"""Review and approval state transitions."""

from __future__ import annotations

from backend.app.collaboration.exceptions import CollaborationError
from backend.app.collaboration.policy import ReviewDecision, ReviewState

DECISION_TO_STATE: dict[str, str] = {
    ReviewDecision.APPROVE.value: ReviewState.APPROVED.value,
    ReviewDecision.REQUEST_CHANGES.value: ReviewState.CHANGES_REQUESTED.value,
    ReviewDecision.REJECT.value: ReviewState.REJECTED.value,
}


def apply_review_decision(current_state: str, decision: str) -> str:
    """Map a review decision onto a deterministic state."""

    if current_state in {
        ReviewState.APPROVED.value,
        ReviewState.REJECTED.value,
        ReviewState.ARCHIVED.value,
    }:
        raise CollaborationError("This review is already finalized.")
    try:
        ReviewDecision(decision)
    except ValueError as exc:
        raise CollaborationError(f"Unknown review decision: {decision}") from exc
    return DECISION_TO_STATE[decision]
