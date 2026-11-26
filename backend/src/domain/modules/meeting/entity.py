from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from src.domain.modules.user.entity import Role, UserRef
from src.domain.shared.numbers import round_half_up


class MeetingSection(StrEnum):
    SCORECARD = "scorecard"
    IDS = "ids"
    CONCLUDE = "conclude"


# Agenda order and target durations (seconds).
AGENDA: tuple[tuple[MeetingSection, int], ...] = (
    (MeetingSection.SCORECARD, 5 * 60),
    (MeetingSection.IDS, 60 * 60),
    (MeetingSection.CONCLUDE, 10 * 60),
)


@dataclass(frozen=True, slots=True)
class Meeting:
    id: str
    team_id: str
    facilitator_id: str
    started_at: datetime
    current_section: MeetingSection
    section_started_at: datetime
    ended_at: datetime | None = None
    state_version: int = 1

    @property
    def is_active(self) -> bool:
        return self.ended_at is None


def average_rating(ratings: Sequence[int]) -> Decimal | None:
    """Mean rating to one decimal, half up; None if nobody rated."""
    if not ratings:
        return None
    return round_half_up(Decimal(sum(ratings)) / len(ratings), 1)


RATING_MIN, RATING_MAX = 1, 10
SECTION_DURATION_S: dict[MeetingSection, int] = dict(AGENDA)
_ORDER = [section for section, _ in AGENDA]


def next_section(section: MeetingSection) -> MeetingSection | None:
    i = _ORDER.index(section)
    return _ORDER[i + 1] if i + 1 < len(_ORDER) else None


@dataclass(frozen=True, slots=True)
class Attendee:
    user: UserRef
    role: Role
    joined_at: datetime

    @property
    def can_rate(self) -> bool:
        return self.role is not Role.OBSERVER


@dataclass(frozen=True, slots=True)
class Rating:
    user_id: str
    rating: int
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class MeetingState:
    """Everything a client needs to render the meeting; the timer is derived from
    `meeting.section_started_at` + the section's duration against the server's now."""

    meeting: Meeting
    facilitator: UserRef
    attendees: tuple[Attendee, ...]
    ratings: tuple[Rating, ...]

    @property
    def average_rating(self) -> Decimal | None:
        return average_rating([r.rating for r in self.ratings])

    @property
    def section_duration_s(self) -> int:
        return SECTION_DURATION_S[self.meeting.current_section]
