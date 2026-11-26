from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from src.domain.modules.todo.entity import Completion, Todo, weekly_completion
from src.domain.shared.calendar import week_bounds_utc

CHI = ZoneInfo("America/Chicago")
NOW = datetime(2026, 11, 11, 15, tzinfo=UTC)
TODAY = date(2026, 11, 11)


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


def todo(due: date, done_at: datetime | None = None) -> Todo:
    return Todo("t", "tm", "u", "x", due_date=due, created_at=utc(2026, 1, 1), done_at=done_at)


def completion(todos: list[Todo], week: date) -> Completion | None:
    _, end = week_bounds_utc(week, CHI)
    return weekly_completion(todos, week_start=week, week_end_utc=end, now=NOW)


def test_exactly_90_percent_meets_target() -> None:
    due = date(2026, 11, 5)
    todos = [todo(due, utc(2026, 11, 4, 12))] * 9 + [todo(due)]
    assert completion(todos, date(2026, 11, 2)) == Completion(10, 9, 90, True)


def test_done_one_minute_either_side_of_week_end() -> None:
    # Week of Nov 2 ends Mon Nov 9 00:00 CST = 06:00Z.
    inside, outside = (
        todo(date(2026, 11, 6), utc(2026, 11, 9, 5, 59)),
        todo(date(2026, 11, 6), utc(2026, 11, 9, 6, 1)),
    )
    c = completion([inside, outside], date(2026, 11, 2))
    assert c is not None and c.done == 1


def test_dst_week_end_counts_late_sunday() -> None:
    # DST ended Nov 1, so the week of Oct 26 ends at 06:00Z; 05:30Z is still inside.
    c = completion([todo(date(2026, 10, 30), utc(2026, 11, 2, 5, 30))], date(2026, 10, 26))
    assert c is not None and c.done == 1


def test_two_of_three_rounds_to_67_and_misses_target() -> None:
    due = date(2026, 10, 27)
    todos = [todo(due, utc(2026, 10, 27, 12))] * 2 + [todo(due)]
    assert completion(todos, date(2026, 10, 26)) == Completion(3, 2, 67, False)


def test_nothing_due_is_none() -> None:
    assert completion([todo(date(2026, 1, 1))], date(2026, 11, 2)) is None


def test_done_after_now_does_not_count() -> None:
    c = completion([todo(date(2026, 11, 9), utc(2026, 11, 12))], date(2026, 11, 9))
    assert c is not None and c.done == 0


def test_overdue_excludes_due_today_and_done() -> None:
    assert todo(date(2026, 11, 10)).is_overdue(today=TODAY, now=NOW)
    assert not todo(TODAY).is_overdue(today=TODAY, now=NOW)
    assert not todo(date(2026, 11, 1), utc(2026, 11, 2)).is_overdue(today=TODAY, now=NOW)
