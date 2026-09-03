"""Comment mention parsing and soft-delete helpers."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from backend.app.models.collaboration import InvestigationComment

_MENTION_PATTERN = re.compile(r"@([A-Za-z0-9_]{3,64})")


def extract_mention_usernames(body: str) -> list[str]:
    """Return unique @username mentions in deterministic order."""

    seen: set[str] = set()
    ordered: list[str] = []
    for match in _MENTION_PATTERN.finditer(body):
        username = match.group(1)
        key = username.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(username)
    return ordered


def soft_delete_comment(comment: InvestigationComment) -> None:
    """Mark a comment deleted without removing forensic linkage."""

    history = list(comment.edit_history_json or [])
    history.append(
        {
            "body": comment.body,
            "edited_at": datetime.now(UTC).isoformat(),
            "action": "soft_delete",
        }
    )
    comment.edit_history_json = history
    comment.body = "[deleted]"
    comment.is_deleted = True


def append_edit_history(comment: InvestigationComment, previous: str) -> None:
    """Record a prior body version when editing."""

    history = list(comment.edit_history_json or [])
    history.append(
        {
            "body": previous,
            "edited_at": datetime.now(UTC).isoformat(),
            "action": "edit",
        }
    )
    comment.edit_history_json = history
