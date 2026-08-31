"""Repository operations for case persistence."""

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.case import Case


class CaseRepository:
    """Encapsulate case queries and persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, case_id: UUID) -> Case | None:
        """Return one case by internal identifier."""

        return await self.session.get(Case, case_id)

    async def list(self, *, limit: int, offset: int) -> tuple[list[Case], int]:
        """Return a bounded, newest-first case page and total count."""

        total = await self.session.scalar(select(func.count()).select_from(Case))
        result = await self.session.scalars(
            select(Case).order_by(Case.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result), int(total or 0)

    async def add(self, case: Case) -> Case:
        """Stage a case for persistence and flush generated state."""

        self.session.add(case)
        await self.session.flush()
        return case

    async def next_case_number(self) -> str:
        """Allocate a public number using a PostgreSQL sequence when available."""

        bind = self.session.get_bind()
        if bind.dialect.name == "postgresql":
            result = await self.session.scalar(
                text("SELECT nextval('case_number_seq')")
            )
            next_number = int(result or 1)
        else:
            result = await self.session.scalar(
                select(Case.case_number).order_by(Case.case_number.desc()).limit(1)
            )
            next_number = int(result.split("-")[-1]) + 1 if result else 1
        return f"CASE-{next_number:06d}"
