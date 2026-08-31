"""Domain port for reliable asynchronous event publication."""

from datetime import datetime
from typing import Protocol
from uuid import UUID


class EventPublisher(Protocol):
    """Port implemented by a broker adapter behind an outbox boundary."""

    async def publish(
        self,
        *,
        event_name: str,
        payload: dict[str, object],
        event_id: UUID | None = None,
        occurred_at: datetime | None = None,
    ) -> UUID:
        """Publish an idempotent event and return its stable identifier."""
        ...
