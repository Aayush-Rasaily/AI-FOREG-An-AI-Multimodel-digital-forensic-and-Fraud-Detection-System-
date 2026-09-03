"""Audit event recorder — writes events to the database."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.events import build_audit_event

logger = logging.getLogger(__name__)


class AuditRecorder:
    """Append audit events to the database."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        operation: str,
        category: str,
        user: str = "system",
        case_id: UUID | None = None,
        evidence_id: UUID | None = None,
        previous_state: Any = None,
        new_state: Any = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        sha256_checksum: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """Create and persist one audit event."""
        from backend.app.models.audit import AuditEvent

        event_data = build_audit_event(
            operation=operation,
            category=category,
            user=user,
            case_id=case_id,
            evidence_id=evidence_id,
            previous_state=previous_state,
            new_state=new_state,
            client_ip=client_ip,
            user_agent=user_agent,
            sha256_checksum=sha256_checksum,
            metadata=metadata,
        )
        record = AuditEvent(
            id=UUID(event_data["id"]),
            timestamp=datetime.fromisoformat(event_data["timestamp"]),
            user=event_data["user"],
            operation=event_data["operation"],
            category=event_data["category"],
            case_id=(
                UUID(event_data["case_id"])
                if event_data["case_id"]
                else None
            ),
            evidence_id=(
                UUID(event_data["evidence_id"])
                if event_data["evidence_id"]
                else None
            ),
            previous_state_json=event_data["previous_state"],
            new_state_json=event_data["new_state"],
            client_ip=event_data["client_ip"],
            user_agent=event_data["user_agent"],
            engine_version=event_data["engine_version"],
            policy_version=event_data["policy_version"],
            sha256_checksum=event_data["sha256_checksum"],
            integrity_hash=event_data["integrity_hash"],
            metadata_json=event_data["metadata"],
        )
        self.session.add(record)
        await self.session.flush()
        logger.info(
            "Audit event recorded",
            extra={
                "audit_id": str(record.id),
                "operation": operation,
            },
        )
        return record.id
