"""Team repository interface (port). Implemented in src.infra.database.repositories."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.domain.modules.team.entity import Team
from src.domain.modules.user.entity import User


class TeamRepository(ABC):
    @abstractmethod
    async def get(self, team_id: str) -> Team | None: ...

    @abstractmethod
    async def list_by_company(self, company_id: str) -> Sequence[Team]: ...

    @abstractmethod
    async def list_for_user(self, user_id: str) -> Sequence[Team]: ...

    @abstractmethod
    async def is_member(self, user_id: str, team_id: str) -> bool: ...

    @abstractmethod
    async def list_members(self, team_id: str) -> Sequence[User]: ...
