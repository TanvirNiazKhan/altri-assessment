"""Issue repository interface (port). Implemented in src.infra.database.repositories."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date, datetime

from src.domain.modules.issue.entity import Issue


class IssueRepository(ABC):
    @abstractmethod
    async def list_open(self, team_id: str) -> Sequence[Issue]:
        """Unsolved Issues in Issue order."""

    @abstractmethod
    async def list_solved(self, team_id: str) -> Sequence[Issue]:
        """Solved Issues, most recently solved first."""

    @abstractmethod
    async def list_all(self, team_id: str) -> Sequence[Issue]: ...

    @abstractmethod
    async def list_solved_in_meeting(self, meeting_id: str) -> Sequence[Issue]: ...

    @abstractmethod
    async def get(self, team_id: str, issue_id: str) -> Issue | None: ...

    @abstractmethod
    async def add(
        self, team_id: str, owner_id: str, title: str, priority: int | None, created_at: datetime
    ) -> Issue: ...

    @abstractmethod
    async def add_from_measurable_or_get(
        self,
        team_id: str,
        owner_id: str,
        title: str,
        created_at: datetime,
        measurable_id: str,
        week_start: date,
    ) -> tuple[Issue, bool]:
        """Atomically create the Issue for (measurable, week) or return the unsolved one.

        Returns (issue, created). Must be race-free across processes.
        """

    @abstractmethod
    async def set_priority(self, team_id: str, issue_id: str, priority: int | None) -> Issue: ...

    @abstractmethod
    async def solve(
        self,
        team_id: str,
        issue_id: str,
        note: str,
        solved_at: datetime,
        meeting_id: str | None,
    ) -> Issue | None:
        """Solve if still unsolved; None if it was already solved."""

    @abstractmethod
    async def open_measurable_issue_ids(self, team_id: str) -> dict[tuple[str, date], str]:
        """(measurable_id, week_start) -> id of its unsolved Issue."""
