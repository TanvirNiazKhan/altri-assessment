"""Company-time calendar math: weeks (Mon-Sun), today, quarter.

All conversions go through zoneinfo, so DST transitions are handled per date.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

WEEK = timedelta(days=7)


def local_date(instant: datetime, tz: ZoneInfo) -> date:
    return instant.astimezone(tz).date()


def week_start_of(instant: datetime, tz: ZoneInfo) -> date:
    """Monday (company time) of the week containing `instant`."""
    d = local_date(instant, tz)
    return d - timedelta(days=d.weekday())


def local_midnight_utc(d: date, tz: ZoneInfo) -> datetime:
    return datetime.combine(d, time.min, tzinfo=tz).astimezone(UTC)


def week_bounds_utc(week_start: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """[start, end) of a week in UTC. End is the next Monday 00:00 local, DST-aware."""
    return local_midnight_utc(week_start, tz), local_midnight_utc(week_start + WEEK, tz)


def quarter_of(d: date) -> str:
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def week_window(current_week: date, weeks: int) -> list[date]:
    """`weeks` Mondays ending with (and including) `current_week`, oldest first."""
    return [current_week - WEEK * i for i in range(weeks - 1, -1, -1)]


@dataclass(frozen=True, slots=True)
class CalendarContext:
    """Everything derived from "now" in company time; computed once per request."""

    now: datetime
    tz: ZoneInfo
    today: date
    current_week: date
    last_closed_week: date
    quarter: str

    @classmethod
    def at(cls, now: datetime, tz: ZoneInfo) -> "CalendarContext":
        current_week = week_start_of(now, tz)
        today = local_date(now, tz)
        return cls(
            now=now,
            tz=tz,
            today=today,
            current_week=current_week,
            last_closed_week=current_week - WEEK,
            quarter=quarter_of(today),
        )
