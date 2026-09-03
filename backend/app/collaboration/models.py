"""Collaboration domain models."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MentionRef:
    """A parsed @username mention."""

    username: str
    user_id: UUID | None = None
