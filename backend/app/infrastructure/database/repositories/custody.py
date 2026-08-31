"""Repository operations for chain-of-custody persistence."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.custody import ChainOfCustodyEvent


class CustodyRepository:
    """Encapsulate append-only custody event persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, event: ChainOfCustodyEvent) -> ChainOfCustodyEvent:
        """Stage one custody event for the current transaction."""

        self.session.add(event)
        await self.session.flush()
        return event
