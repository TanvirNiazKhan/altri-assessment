from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from src.domain.shared.numbers import round_half_up

COMPLETION_TARGET_NUM, COMPLETION_TARGET_DEN = 9, 10  # 90 %


@dataclass(frozen=True, slots=True)
class Todo:
    id: str
    team_id: str
    owner_id: str
    title: str
    due_date: date
    created_at: datetime
    done_at: datetime | None = None
    source_issue_id: str | None = None
    created_in_meeting_id: str | None = None

    def is_done_as_of(self, now: datetime) -> bool:
        return self.done_at is not None and self.done_at <= now

    def is_overdue(self, *, today: date, now: datetime) -> bool:
        return not self.is_done_as_of(now) and self.due_date < today


@dataclass(frozen=True, slots=True)
class Completion:
    due: int
    done: int
    rate_percent: int
    meets_target: bool


def weekly_completion(
    todos: Iterable[Todo], *, week_start: date, week_end_utc: datetime, now: datetime
) -> Completion | None:
    """Completion for one week; None when nothing was due.

    `week_end_utc` is the next Monday 00:00 company time (exclusive). A To-Do counts as
    done if it was done before that instant and no later than `now`.
    """
    week_end = week_start + timedelta(days=7)
    due = [t for t in todos if week_start <= t.due_date < week_end]
    if not due:
        return None
    done = sum(
        1
        for t in due
        if t.done_at is not None and t.done_at < week_end_utc and t.is_done_as_of(now)
    )
    return Completion(
        due=len(due),
        done=done,
        rate_percent=int(round_half_up(Decimal(100 * done) / len(due))),
        # Exact integer comparison against 90 %, not the rounded percent.
        meets_target=done * COMPLETION_TARGET_DEN >= len(due) * COMPLETION_TARGET_NUM,
    )


TODO_TITLE_MAX = 200
TODO_DUE_IN_DAYS = 7


@dataclass(frozen=True, slots=True)
class TodoView:
    todo: Todo
    owner_name: str
    overdue: bool
    source_issue_title: str | None = None


@dataclass(frozen=True, slots=True)
class WeeklyCompletion:
    week_start: date
    completion: Completion | None


@dataclass(frozen=True, slots=True)
class TodoList:
    items: tuple[TodoView, ...]
    last_closed_week: WeeklyCompletion
