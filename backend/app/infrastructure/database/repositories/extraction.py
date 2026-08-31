"""Repository operations for searchable extraction records."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.extraction.models import ExtractionType
from backend.app.models.extraction import ExtractionRecord


class ExtractionRepository:
    """Encapsulate bounded extraction-record queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, extraction_id: UUID) -> ExtractionRecord | None:
        """Return one extraction record."""

        return await self.session.get(ExtractionRecord, extraction_id)

    async def list_for_evidence(
        self,
        evidence_id: UUID,
        *,
        extraction_type: ExtractionType | Sequence[ExtractionType] | None,
        limit: int,
        offset: int,
    ) -> tuple[list[ExtractionRecord], int]:
        """Return a bounded extraction page for one evidence item."""

        filters = [ExtractionRecord.evidence_id == evidence_id]
        if extraction_type is not None:
            if isinstance(extraction_type, ExtractionType):
                filters.append(ExtractionRecord.extraction_type == extraction_type)
            else:
                filters.append(ExtractionRecord.extraction_type.in_(extraction_type))
        total = await self.session.scalar(
            select(func.count()).select_from(ExtractionRecord).where(*filters)
        )
        result = await self.session.scalars(
            select(ExtractionRecord)
            .where(*filters)
            .order_by(ExtractionRecord.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def add(self, record: ExtractionRecord) -> ExtractionRecord:
        """Stage and flush a record."""

        self.session.add(record)
        await self.session.flush()
        return record
