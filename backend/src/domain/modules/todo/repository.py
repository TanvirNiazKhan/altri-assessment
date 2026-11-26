"""To-Do repository interface (port). Implemented in src.infra.database.repositories."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date, datetime

from src.domain.modules.todo.entity import Todo


class TodoRepository(ABC):
    @abstractmethod
    async def list(self, team_id: str) -> Sequence[Todo]:
        """All of a team's To-Dos, by due date then id."""

    @abstractmethod
    async def list_created_in_meeting(self, meeting_id: str) -> Sequence[Todo]: ...

    @abstractmethod
    async def get(self, team_id: str, todo_id: str) -> Todo | None: ...

    @abstractmethod
    async def add(
        self,
        *,
        team_id: str,
        owner_id: str,
        title: str,
        due_date: date,
        created_at: datetime,
        source_issue_id: str | None,
        created_in_meeting_id: str | None,
    ) -> Todo: ...

    @abstractmethod
    async def set_done_at(self, team_id: str, todo_id: str, done_at: datetime | None) -> Todo: ...

    @abstractmethod
    async def issue_titles(self, issue_ids: Sequence[str]) -> dict[str, str]: ...
