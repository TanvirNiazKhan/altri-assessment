"""Meeting summary: what the team reviewed and decided. Built once when the meeting ends
and stored as a snapshot, so later edits to scores, titles or ratings never change it."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from src.domain.modules.scorecard.entity import MeasurableStatus
from src.domain.modules.user.entity import UserRef
from src.domain.shared.calendar import WEEK, week_start_of


def scorecard_week_for(started_at: datetime, tz: ZoneInfo) -> date:
    """The week a meeting reviews: the last closed week at the time it started."""
    return week_start_of(started_at, tz) - WEEK


@dataclass(frozen=True, slots=True)
class SummaryMeasurable:
    id: str
    name: str
    unit: str
    value: Decimal | None
    status: MeasurableStatus


@dataclass(frozen=True, slots=True)
class SummaryIssue:
    id: str
    title: str
    resolution_note: str | None


@dataclass(frozen=True, slots=True)
class SummaryTodo:
    id: str
    title: str
    owner: UserRef
    due_date: date


@dataclass(frozen=True, slots=True)
class SummaryRating:
    user: UserRef
    rating: int


@dataclass(frozen=True, slots=True)
class MeetingSummary:
    meeting_id: str
    team_id: str
    facilitator: UserRef
    started_at: datetime
    ended_at: datetime
    scorecard_week: date
    measurables: tuple[SummaryMeasurable, ...]
    issues_solved: tuple[SummaryIssue, ...]
    todos_created: tuple[SummaryTodo, ...]
    attendees: tuple[UserRef, ...]
    ratings: tuple[SummaryRating, ...]
    average_rating: Decimal | None
