"""Pydantic contracts for chain-of-custody responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.app.domain.custody import CustodyActorType, CustodyEventType


class CustodyEventResponse(BaseModel):
    """Public chain-of-custody event representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evidence_id: UUID
    event_type: CustodyEventType
    timestamp: datetime
    actor_type: CustodyActorType
    actor_id: str | None
    description: str
    sha256_hash: str
    metadata: dict[str, object]
