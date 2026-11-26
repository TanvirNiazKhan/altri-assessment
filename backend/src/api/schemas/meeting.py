from datetime import date, datetime

from pydantic import Field

from src.api.schemas.common import Number, RequestSchema, ResponseSchema, UserRefResponse
from src.domain.modules.meeting.entity import (
    AGENDA,
    RATING_MAX,
    RATING_MIN,
    Meeting,
    MeetingSection,
    MeetingState,
)
from src.domain.modules.meeting.summary import MeetingSummary
from src.domain.modules.scorecard.entity import MeasurableStatus
from src.domain.modules.user.entity import Role


class AgendaItemResponse(ResponseSchema):
    section: MeetingSection
    duration_s: int


AGENDA_RESPONSE = [AgendaItemResponse(section=s, duration_s=d) for s, d in AGENDA]


class AttendeeResponse(ResponseSchema):
    id: str
    name: str
    role: Role
    joined_at: datetime
    can_rate: bool


class RatingResponse(ResponseSchema):
    user_id: str
    rating: int


class MeetingResponse(ResponseSchema):
    id: str
    team_id: str
    facilitator: UserRefResponse
    started_at: datetime
    ended_at: datetime | None
    current_section: MeetingSection
    section_started_at: datetime
    section_duration_s: int
    state_version: int
    agenda: list[AgendaItemResponse]
    attendees: list[AttendeeResponse]
    ratings: list[RatingResponse]
    average_rating: Number | None

    @classmethod
    def from_domain(cls, s: MeetingState) -> "MeetingResponse":
        m = s.meeting
        return cls(
            id=m.id,
            team_id=m.team_id,
            facilitator=UserRefResponse(id=s.facilitator.id, name=s.facilitator.name),
            started_at=m.started_at,
            ended_at=m.ended_at,
            current_section=m.current_section,
            section_started_at=m.section_started_at,
            section_duration_s=s.section_duration_s,
            state_version=m.state_version,
            agenda=AGENDA_RESPONSE,
            attendees=[
                AttendeeResponse(
                    id=a.user.id,
                    name=a.user.name,
                    role=a.role,
                    joined_at=a.joined_at,
                    can_rate=a.can_rate,
                )
                for a in s.attendees
            ],
            ratings=[RatingResponse(user_id=r.user_id, rating=r.rating) for r in s.ratings],
            average_rating=s.average_rating,
        )


class MeetingStateResponse(ResponseSchema):
    """`server_now` lets clients render the server-owned timer without trusting their clock:
    elapsed = (client_now + (server_now - client_now_at_receipt)) - section_started_at."""

    meeting: MeetingResponse | None
    server_now: datetime

    @classmethod
    def build(cls, state: MeetingState | None, now: datetime) -> "MeetingStateResponse":
        return cls(meeting=MeetingResponse.from_domain(state) if state else None, server_now=now)


class MeetingListItemResponse(ResponseSchema):
    id: str
    started_at: datetime
    ended_at: datetime | None

    @classmethod
    def from_domain(cls, m: Meeting) -> "MeetingListItemResponse":
        return cls(id=m.id, started_at=m.started_at, ended_at=m.ended_at)


class AdvanceRequest(RequestSchema):
    """The section the client believes is current; a stale value is rejected with 409."""

    expected_section: MeetingSection


class RatingRequest(RequestSchema):
    rating: int = Field(ge=RATING_MIN, le=RATING_MAX)


class SummaryMeasurableResponse(ResponseSchema):
    id: str
    name: str
    unit: str
    value: Number | None
    status: MeasurableStatus


class SummaryIssueResponse(ResponseSchema):
    id: str
    title: str
    resolution_note: str | None


class SummaryTodoResponse(ResponseSchema):
    id: str
    title: str
    owner: UserRefResponse
    due_date: date


class SummaryRatingResponse(ResponseSchema):
    user: UserRefResponse
    rating: int


class MeetingSummaryResponse(ResponseSchema):
    meeting_id: str
    team_id: str
    facilitator: UserRefResponse
    started_at: datetime
    ended_at: datetime
    scorecard_week: date
    measurables: list[SummaryMeasurableResponse]
    issues_solved: list[SummaryIssueResponse]
    todos_created: list[SummaryTodoResponse]
    attendees: list[UserRefResponse]
    ratings: list[SummaryRatingResponse]
    average_rating: Number | None

    @classmethod
    def from_domain(cls, s: MeetingSummary) -> "MeetingSummaryResponse":
        return cls.model_validate(s, from_attributes=True)
