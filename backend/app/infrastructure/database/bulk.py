"""Shared bulk persistence helpers (Phase 10C)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


async def bulk_add(
    session: AsyncSession,
    items: Sequence[Any],
    *,
    flush: bool = True,
) -> int:
    """Stage many ORM instances with a single optional flush."""

    if not items:
        return 0
    session.add_all(list(items))
    if flush:
        await session.flush()
    return len(items)


async def bulk_update_mappings(
    session: AsyncSession,
    model: type[Any],
    mappings: Sequence[dict[str, Any]],
) -> int:
    """Apply bulk UPDATE mappings without per-row SELECT."""

    payload = list(mappings)
    if not payload:
        return 0

    def _apply(sync_session: Session) -> None:
        sync_session.bulk_update_mappings(model, payload)

    await session.run_sync(_apply)
    return len(payload)
