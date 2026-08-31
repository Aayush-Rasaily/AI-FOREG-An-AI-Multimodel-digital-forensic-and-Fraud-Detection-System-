"""Application service for case lifecycle operations."""

import logging
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas.case import (
    CaseCreateRequest,
    CaseListResponse,
    CaseResponse,
    CaseUpdateRequest,
)
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.domain.case import CaseStatus
from backend.app.infrastructure.database.repositories.case import CaseRepository
from backend.app.models.case import Case

logger = logging.getLogger(__name__)


class CaseService:
    """Coordinate case use cases without exposing ORM objects to the API."""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = CaseRepository(session)
        self.session = session

    async def create(self, payload: CaseCreateRequest) -> CaseResponse:
        """Create a case with a server-generated public case number."""

        case = Case(
            id=uuid4(),
            case_number=await self.repository.next_case_number(),
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            status=CaseStatus.OPEN,
            created_by="SYSTEM",
        )
        try:
            await self.repository.add(case)
            await self.session.commit()
            await self.session.refresh(case)
        except Exception:
            await self.session.rollback()
            raise

        logger.info("Case created", extra={"case_number": case.case_number})
        return CaseResponse.model_validate(case)

    async def list(self, *, limit: int, offset: int) -> CaseListResponse:
        """Return a bounded page of cases."""

        cases, total = await self.repository.list(limit=limit, offset=offset)
        return CaseListResponse(
            items=[CaseResponse.model_validate(case) for case in cases],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get(self, case_id: UUID) -> CaseResponse:
        """Return one case or raise a public not-found error."""

        case = await self.repository.get(case_id)
        if case is None:
            raise ResourceNotFoundError("The requested case was not found.")
        return CaseResponse.model_validate(case)

    async def update(
        self,
        case_id: UUID,
        payload: CaseUpdateRequest,
    ) -> CaseResponse:
        """Apply only explicitly supplied mutable case fields."""

        case = await self.repository.get(case_id)
        if case is None:
            raise ResourceNotFoundError("The requested case was not found.")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(case, field, value)

        try:
            await self.session.commit()
            await self.session.refresh(case)
        except Exception:
            await self.session.rollback()
            raise
        return CaseResponse.model_validate(case)
