from datetime import date, datetime

from src.api.schemas.common import ResponseSchema
from src.api.schemas.team import TeamResponse
from src.api.schemas.user import UserResponse
from src.domain.shared.calendar import CalendarContext


class CalendarResponse(ResponseSchema):
    now: datetime
    today: date
    current_week: date
    last_closed_week: date
    quarter: str
    timezone: str

    @classmethod
    def from_context(cls, cal: CalendarContext) -> "CalendarResponse":
        return cls(
            now=cal.now,
            today=cal.today,
            current_week=cal.current_week,
            last_closed_week=cal.last_closed_week,
            quarter=cal.quarter,
            timezone=cal.tz.key,
        )


class MeResponse(ResponseSchema):
    user: UserResponse
    teams: list[TeamResponse]
    calendar: CalendarResponse
