"""Rock repository interface (port). Implemented in src.infra.database.repositories."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.domain.modules.rock.entity import Rock


class RockRepository(ABC):
    @abstractmethod
    async def list_for_quarter(self, team_id: str, quarter: str) -> Sequence[Rock]:
        """Rocks with their Milestones loaded, by id."""
