"""Domain port for immutable chain-of-custody audit records."""

from datetime import datetime
from typing import Protocol
from uuid import UUID


class AuditLog(Protocol):
    """Port for append-only, tamper-evident audit storage."""

    async def append(
        self,
        *,
        event_name: str,
        actor_id: str | None,
        tenant_id: str | None,
        resource_id: str | None,
        occurred_at: datetime,
        correlation_id: UUID | None,
        metadata: dict[str, object],
    ) -> UUID:
        """Append an audit record and return its immutable identifier."""
        ...
