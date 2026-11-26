"""Change notifications for real-time clients (port).

Services publish an event in the same transaction as the write; the implementation
delivers it only after commit, so clients never see uncommitted changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum


class Topic(StrEnum):
    MEETING = "meeting"
    SCORECARD = "scorecard"
    ISSUES = "issues"
    TODOS = "todos"


@dataclass(frozen=True, slots=True)
class TeamEvent:
    team_id: str
    topics: frozenset[Topic]
    meeting_id: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: TeamEvent) -> None: ...
