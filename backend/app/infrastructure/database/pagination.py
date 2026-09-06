"""Shared SQLAlchemy pagination helpers (Phase 10C)."""

from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

T = TypeVar("T")


def apply_pagination(
    stmt: Select[Any],
    *,
    limit: int,
    offset: int,
) -> Select[Any]:
    """Apply limit/offset with deterministic bounds."""

    safe_limit = max(1, min(int(limit), 500))
    safe_offset = max(0, int(offset))
    return stmt.limit(safe_limit).offset(safe_offset)


async def count_rows(
    session: AsyncSession,
    stmt: Select[Any],
) -> int:
    """Return the number of rows for a selectable (subquery count)."""

    counted = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    return int(counted or 0)


def order_by_desc(
    stmt: Select[Any],
    column: ColumnElement[Any],
) -> Select[Any]:
    """Order by a column descending (shared helper for list endpoints)."""

    return stmt.order_by(column.desc())
