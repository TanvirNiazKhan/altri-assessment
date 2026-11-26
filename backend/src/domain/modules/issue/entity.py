from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class IssueSourceType(StrEnum):
    MEASURABLE = "measurable"
    ROCK = "rock"


@dataclass(frozen=True, slots=True)
class IssueSource:
    type: IssueSourceType
    measurable_id: str | None = None
    week_start: date | None = None
    rock_id: str | None = None


@dataclass(frozen=True, slots=True)
class Issue:
    id: str
    team_id: str
    owner_id: str
    title: str
    created_at: datetime
    priority: int | None = None
    solved_at: datetime | None = None
    resolution_note: str | None = None
    source: IssueSource | None = None
    solved_in_meeting_id: str | None = None
    version: int = 1

    def is_open_as_of(self, now: datetime) -> bool:
        return self.created_at <= now and (self.solved_at is None or self.solved_at > now)

    def order_key(self) -> tuple[bool, int, datetime, str]:
        """Priority high->low, no priority last, then oldest first, then id (deterministic)."""
        return (self.priority is None, -(self.priority or 0), self.created_at, self.id)


def order_issues(issues: Iterable[Issue]) -> list[Issue]:
    return sorted(issues, key=Issue.order_key)


ISSUE_TITLE_MAX = 200
NOTE_MAX = 2000
PRIORITY_MIN, PRIORITY_MAX = 1, 5


@dataclass(frozen=True, slots=True)
class IssueView:
    """Issue enriched for display: owner name and source Measurable name."""

    issue: Issue
    owner_name: str
    source_measurable_name: str | None = None
