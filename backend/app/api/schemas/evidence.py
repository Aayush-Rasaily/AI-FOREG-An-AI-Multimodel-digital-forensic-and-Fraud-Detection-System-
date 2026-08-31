"""Pydantic contracts for evidence management APIs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.api.schemas.custody import CustodyEventResponse
from backend.app.domain.evidence import EvidenceStatus


class EvidenceResponse(BaseModel):
    """Public evidence metadata without physical storage paths."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    evidence_number: str
    original_filename: str
    stored_filename: str
    mime_type: str
    file_size: int
    sha256_hash: str
    status: EvidenceStatus
    metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime
    custody_events: list[CustodyEventResponse] = Field(default_factory=list)


class EvidenceListResponse(BaseModel):
    """Evidence collection for one case."""

    items: list[EvidenceResponse]
    total: int
