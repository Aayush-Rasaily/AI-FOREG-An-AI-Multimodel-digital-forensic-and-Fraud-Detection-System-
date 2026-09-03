"""Audit event persistence queries."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit import AuditEvent


class AuditRepository:
    """Database operations for audit events."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_event(
        self, event_id: UUID,
    ) -> AuditEvent | None:
        return await self.session.get(AuditEvent, event_id)

    async def list_events(
        self,
        *,
        case_id: UUID | None = None,
        evidence_id: UUID | None = None,
        operation: str | None = None,
        category: str | None = None,
        user: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditEvent], int]:
        filters = []
        if case_id is not None:
            filters.append(AuditEvent.case_id == case_id)
        if evidence_id is not None:
            filters.append(AuditEvent.evidence_id == evidence_id)
        if operation is not None:
            filters.append(AuditEvent.operation == operation)
        if category is not None:
            filters.append(AuditEvent.category == category)
        if user is not None:
            filters.append(AuditEvent.user == user)
        total = await self.session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(*filters)
            if filters
            else select(func.count()).select_from(AuditEvent)
        )
        query = (
            select(AuditEvent)
            .order_by(AuditEvent.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        if filters:
            query = query.where(*filters)
        result = await self.session.scalars(query)
        return list(result), int(total or 0)

    async def list_for_case(
        self,
        case_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditEvent], int]:
        return await self.list_events(
            case_id=case_id, limit=limit, offset=offset,
        )

    async def list_for_evidence(
        self,
        evidence_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditEvent], int]:
        return await self.list_events(
            evidence_id=evidence_id, limit=limit, offset=offset,
        )
