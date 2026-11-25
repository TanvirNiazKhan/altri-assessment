from collections.abc import Iterable, Sequence

from sqlalchemy import select

from src.domain.modules.user.entity import User
from src.domain.modules.user.repository import UserRepository
from src.infra.database.models import UserModel
from src.infra.database.repositories.base import SqlRepository
from src.infra.database.repositories.mappers import to_user


class SqlUserRepository(SqlRepository, UserRepository):
    async def get(self, user_id: str) -> User | None:
        m = await self._s.get(UserModel, user_id)
        return to_user(m) if m else None

    async def list_all(self) -> Sequence[User]:
        rows = await self._s.scalars(select(UserModel).order_by(UserModel.name, UserModel.id))
        return [to_user(m) for m in rows]

    async def get_many(self, user_ids: Iterable[str]) -> dict[str, User]:
        ids = set(user_ids)
        if not ids:
            return {}
        rows = await self._s.scalars(select(UserModel).where(UserModel.id.in_(ids)))
        return {m.id: to_user(m) for m in rows}
