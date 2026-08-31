"""Repository operations for evidence persistence."""

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.evidence import Evidence


class EvidenceRepository:
    """Encapsulate evidence queries and persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, evidence_id: UUID) -> Evidence | None:
        """Return evidence metadata with its custody history."""

        return await self.session.scalar(
            select(Evidence)
            .options(selectinload(Evidence.custody_events))
            .where(Evidence.id == evidence_id)
        )

    async def list_for_case(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Evidence], int]:
        """Return a bounded evidence page and total for one case."""

        total = await self.session.scalar(
            select(func.count())
            .select_from(Evidence)
            .where(Evidence.case_id == case_id)
        )
        result = await self.session.scalars(
            select(Evidence)
            .where(Evidence.case_id == case_id)
            .order_by(Evidence.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result), int(total or 0)

    async def get_by_hash(self, case_id: UUID, sha256_hash: str) -> Evidence | None:
        """Return a case's evidence with the given immutable hash."""

        return await self.session.scalar(
            select(Evidence).where(
                Evidence.case_id == case_id,
                Evidence.sha256_hash == sha256_hash,
            )
        )

    async def add(self, evidence: Evidence) -> Evidence:
        """Stage evidence metadata for persistence."""

        self.session.add(evidence)
        await self.session.flush()
        return evidence

    async def next_evidence_number(self) -> str:
        """Allocate a public number using a PostgreSQL sequence when available."""

        bind = self.session.get_bind()
        if bind.dialect.name == "postgresql":
            result = await self.session.scalar(
                text("SELECT nextval('evidence_number_seq')")
            )
            next_number = int(result or 1)
        else:
            result = await self.session.scalar(
                select(Evidence.evidence_number)
                .order_by(Evidence.evidence_number.desc())
                .limit(1)
            )
            next_number = int(result.split("-")[-1]) + 1 if result else 1
        return f"EVID-{next_number:06d}"
