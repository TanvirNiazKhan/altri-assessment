"""User repository interface (port). Implemented in src.infra.database.repositories."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence

from src.domain.modules.user.entity import User


class UserRepository(ABC):
    @abstractmethod
    async def get(self, user_id: str) -> User | None: ...

    @abstractmethod
    async def list_all(self) -> Sequence[User]: ...

    @abstractmethod
    async def get_many(self, user_ids: Iterable[str]) -> dict[str, User]: ...
