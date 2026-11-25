from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from src.domain.shared.calendar import (
    CalendarContext,
    quarter_of,
    week_bounds_utc,
    week_start_of,
    week_window,
)

CHI = ZoneInfo("America/Chicago")


def test_week_end_moves_with_dst() -> None:
    # CDT (UTC-5) before Nov 1, CST (UTC-6) after.
    assert week_bounds_utc(date(2026, 10, 19), CHI) == (
        datetime(2026, 10, 19, 5, tzinfo=UTC),
        datetime(2026, 10, 26, 5, tzinfo=UTC),
    )
    assert week_bounds_utc(date(2026, 10, 26), CHI)[1] == datetime(2026, 11, 2, 6, tzinfo=UTC)


def test_week_start_uses_company_time() -> None:
    # Sun Nov 1 23:30 CST is still the week of Oct 26.
    assert week_start_of(datetime(2026, 11, 2, 5, 30, tzinfo=UTC), CHI) == date(2026, 10, 26)
    assert week_start_of(datetime(2026, 11, 2, 6, 0, tzinfo=UTC), CHI) == date(2026, 11, 2)


def test_calendar_at_seed_now() -> None:
    cal = CalendarContext.at(datetime(2026, 11, 11, 15, tzinfo=UTC), CHI)
    assert (cal.today, cal.current_week, cal.last_closed_week, cal.quarter) == (
        date(2026, 11, 11),
        date(2026, 11, 9),
        date(2026, 11, 2),
        "2026-Q4",
    )


def test_thirteen_week_window() -> None:
    w = week_window(date(2026, 11, 9), 13)
    assert (len(w), w[0], w[-1]) == (13, date(2026, 8, 17), date(2026, 11, 9))


def test_quarter_of() -> None:
    assert quarter_of(date(2026, 1, 1)) == "2026-Q1"
    assert quarter_of(date(2026, 12, 31)) == "2026-Q4"
