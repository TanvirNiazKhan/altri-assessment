from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.shared.unit_of_work import UnitOfWork
from src.infra.database.errors import translate_db_errors


class SqlUnitOfWork(UnitOfWork):
    """Commits the request's session. Shares the session with that request's repositories."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def commit(self) -> None:
        async with translate_db_errors():
            await self._s.commit()

    async def rollback(self) -> None:
        await self._s.rollback()
