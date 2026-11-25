from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database.errors import translate_db_errors


class SqlRepository:
    """Shared plumbing for SQL repositories. Writes go through `_flush()` so constraint
    violations surface as domain errors at the point of the write."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def _flush(self) -> None:
        async with translate_db_errors():
            await self._s.flush()
