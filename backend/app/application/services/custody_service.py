"""Application service for append-only chain-of-custody events."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas.custody import CustodyEventResponse
from backend.app.domain.custody import CustodyActorType, CustodyEventType
from backend.app.infrastructure.database.repositories.custody import CustodyRepository
from backend.app.models.custody import ChainOfCustodyEvent


class ChainOfCustodyService:
    """Create custody records without exposing persistence concerns to routes."""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = CustodyRepository(session)

    async def record_ingestion(
        self,
        *,
        evidence_id: UUID,
        sha256_hash: str,
        timestamp: datetime | None = None,
    ) -> CustodyEventResponse:
        """Record the initial SYSTEM evidence-ingested event."""

        event = ChainOfCustodyEvent(
            id=uuid4(),
            evidence_id=evidence_id,
            event_type=CustodyEventType.EVIDENCE_INGESTED,
            timestamp=timestamp or datetime.now(UTC),
            actor_type=CustodyActorType.SYSTEM,
            actor_id=None,
            description="Evidence ingested and original bytes preserved.",
            sha256_hash=sha256_hash,
            metadata_json={},
        )
        await self.repository.add(event)
        return self.to_response(event)

    @staticmethod
    def to_response(event: ChainOfCustodyEvent) -> CustodyEventResponse:
        """Map an ORM event without touching SQLAlchemy's reserved metadata."""

        return CustodyEventResponse(
            id=event.id,
            evidence_id=event.evidence_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            description=event.description,
            sha256_hash=event.sha256_hash,
            metadata=event.metadata_json,
        )
