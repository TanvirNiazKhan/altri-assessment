"""Level 10 meeting use cases.

Postgres holds all meeting state; every transition is a conditional update, so double
clicks, stale tabs and concurrent requests cannot skip sections or start two meetings.
"""

from collections.abc import Sequence
from zoneinfo import ZoneInfo

from src.domain.modules.issue.repository import IssueRepository
from src.domain.modules.meeting.entity import (
    Attendee,
    Meeting,
    MeetingSection,
    MeetingState,
    average_rating,
    next_section,
)
from src.domain.modules.meeting.exceptions import (
    MeetingAlreadyActiveError,
    MeetingEndedError,
    MeetingNotEndedError,
    MeetingNotFoundError,
    NoNextSectionError,
    NotAttendeeError,
    NotFacilitatorError,
    RatingNotOpenError,
    SectionConflictError,
)
from src.domain.modules.meeting.repository import MeetingRepository
from src.domain.modules.meeting.summary import (
    MeetingSummary,
    SummaryIssue,
    SummaryMeasurable,
    SummaryRating,
    SummaryTodo,
    scorecard_week_for,
)
from src.domain.modules.scorecard.repository import ScorecardRepository
from src.domain.modules.scorecard.service import statuses_for_week
from src.domain.modules.team.entity import TeamAccess
from src.domain.modules.todo.repository import TodoRepository
from src.domain.modules.user.entity import ref_for
from src.domain.modules.user.repository import UserRepository
from src.domain.shared.calendar import WEEK, CalendarContext
from src.domain.shared.events import EventPublisher, TeamEvent, Topic
from src.domain.shared.unit_of_work import UnitOfWork


class MeetingService:
    def __init__(
        self,
        meetings: MeetingRepository,
        scorecard: ScorecardRepository,
        issues: IssueRepository,
        todos: TodoRepository,
        users: UserRepository,
        uow: UnitOfWork,
        events: EventPublisher,
    ) -> None:
        self._meetings = meetings
        self._scorecard = scorecard
        self._issues = issues
        self._todos = todos
        self._users = users
        self._uow = uow
        self._events = events

    # ------------------------------------------------------------------ reads

    async def active_state(self, team_id: str) -> MeetingState | None:
        meeting = await self._meetings.get_active(team_id)
        return await self._state(meeting) if meeting else None

    async def state(self, team_id: str, meeting_id: str) -> MeetingState:
        return await self._state(await self._require(team_id, meeting_id))

    async def list_ended(self, team_id: str) -> Sequence[Meeting]:
        return await self._meetings.list_ended(team_id)

    async def summary(self, team_id: str, meeting_id: str, tz: ZoneInfo) -> MeetingSummary:
        meeting = await self._require(team_id, meeting_id)
        if meeting.ended_at is None:
            raise MeetingNotEndedError()
        stored = await self._meetings.get_summary(meeting.id)
        return stored or await self.build_summary(meeting, tz)

    # ------------------------------------------------------------------ commands

    async def start(self, access: TeamAccess, cal: CalendarContext) -> MeetingState:
        """The starter becomes facilitator and first attendee."""
        active = await self._meetings.get_active(access.team.id)
        if active is not None:
            raise MeetingAlreadyActiveError(details={"meeting_id": active.id})
        # A concurrent start that slips past the check fails on the partial unique index.
        meeting = await self._meetings.create(access.team.id, access.user.id, cal.now)
        await self._meetings.add_attendee(meeting.id, access.user.id, cal.now)
        await self._commit(access.team.id, meeting.id)
        return await self.state(access.team.id, meeting.id)

    async def join(self, access: TeamAccess, meeting_id: str, cal: CalendarContext) -> MeetingState:
        """Anyone who can read the team may join (Observers included). Idempotent."""
        meeting = await self._require_active(access.team.id, meeting_id)
        if await self._meetings.add_attendee(meeting.id, access.user.id, cal.now):
            await self._commit(access.team.id, meeting.id)
        return await self.state(access.team.id, meeting.id)

    async def advance(
        self,
        access: TeamAccess,
        meeting_id: str,
        expected: MeetingSection,
        cal: CalendarContext,
    ) -> MeetingState:
        meeting = await self._require_active(access.team.id, meeting_id)
        self._require_facilitator(meeting, access)
        if meeting.current_section is not expected:
            raise SectionConflictError(details={"current_section": meeting.current_section})
        target = next_section(expected)
        if target is None:
            raise NoNextSectionError()
        updated = await self._meetings.advance(
            access.team.id,
            meeting_id,
            facilitator_id=access.user.id,
            expected=expected,
            to=target,
            now=cal.now,
        )
        if updated is None:  # lost a race with another advance or the end
            raise SectionConflictError()
        await self._commit(access.team.id, meeting_id)
        return await self.state(access.team.id, meeting_id)

    async def end(self, access: TeamAccess, meeting_id: str, cal: CalendarContext) -> MeetingState:
        """Facilitator ends the meeting at any time; the summary is frozen in the same commit."""
        meeting = await self._require_active(access.team.id, meeting_id)
        self._require_facilitator(meeting, access)
        ended = await self._meetings.end(
            access.team.id, meeting_id, facilitator_id=access.user.id, now=cal.now
        )
        if ended is None:
            raise MeetingEndedError()
        await self._meetings.save_summary(await self.build_summary(ended, cal.tz), cal.now)
        await self._events.publish(
            TeamEvent(
                access.team.id,
                frozenset({Topic.MEETING, Topic.ISSUES, Topic.TODOS}),
                meeting_id=meeting_id,
            )
        )
        await self._uow.commit()
        return await self.state(access.team.id, meeting_id)

    async def rate(
        self, access: TeamAccess, meeting_id: str, rating: int, cal: CalendarContext
    ) -> MeetingState:
        """Attending Admins / Team Members rate 1-10 during Conclude; changeable until the end."""
        meeting = await self._require_active(access.team.id, meeting_id)
        if meeting.current_section is not MeetingSection.CONCLUDE:
            raise RatingNotOpenError()
        attendee_ids = {uid for uid, _ in await self._meetings.list_attendees(meeting.id)}
        if access.user.id not in attendee_ids:
            raise NotAttendeeError()
        await self._meetings.upsert_rating(meeting.id, access.user.id, rating, cal.now)
        await self._commit(access.team.id, meeting.id)
        return await self.state(access.team.id, meeting.id)

    # ------------------------------------------------------------------ summary

    async def build_summary(self, meeting: Meeting, tz: ZoneInfo) -> MeetingSummary:
        if meeting.ended_at is None:
            raise MeetingNotEndedError()
        week = scorecard_week_for(meeting.started_at, tz)
        # Judged as of the meeting's own week, so the reviewed week counts as closed.
        statuses = await statuses_for_week(
            self._scorecard, meeting.team_id, week, current_week=week + WEEK
        )
        solved = await self._issues.list_solved_in_meeting(meeting.id)
        created = await self._todos.list_created_in_meeting(meeting.id)
        attendees = await self._meetings.list_attendees(meeting.id)
        ratings = await self._meetings.list_ratings(meeting.id)
        users = await self._users.get_many(
            [meeting.facilitator_id]
            + [uid for uid, _ in attendees]
            + [t.owner_id for t in created]
            + [r.user_id for r in ratings]
        )
        return MeetingSummary(
            meeting_id=meeting.id,
            team_id=meeting.team_id,
            facilitator=ref_for(users, meeting.facilitator_id),
            started_at=meeting.started_at,
            ended_at=meeting.ended_at,
            scorecard_week=week,
            measurables=tuple(
                SummaryMeasurable(id=m.id, name=m.name, unit=m.unit, value=v, status=s)
                for m, v, s in statuses
            ),
            issues_solved=tuple(
                SummaryIssue(id=i.id, title=i.title, resolution_note=i.resolution_note)
                for i in sorted(solved, key=lambda i: i.id)
            ),
            todos_created=tuple(
                SummaryTodo(
                    id=t.id, title=t.title, owner=ref_for(users, t.owner_id), due_date=t.due_date
                )
                for t in sorted(created, key=lambda t: t.id)
            ),
            attendees=tuple(ref_for(users, uid) for uid in sorted(uid for uid, _ in attendees)),
            ratings=tuple(
                SummaryRating(user=ref_for(users, r.user_id), rating=r.rating)
                for r in sorted(ratings, key=lambda r: r.user_id)
            ),
            average_rating=average_rating([r.rating for r in ratings]),
        )

    # ------------------------------------------------------------------ helpers

    async def _state(self, meeting: Meeting) -> MeetingState:
        attendees = await self._meetings.list_attendees(meeting.id)
        ratings = await self._meetings.list_ratings(meeting.id)
        users = await self._users.get_many([meeting.facilitator_id, *(u for u, _ in attendees)])
        return MeetingState(
            meeting=meeting,
            facilitator=ref_for(users, meeting.facilitator_id),
            attendees=tuple(
                Attendee(user=ref_for(users, uid), role=users[uid].role, joined_at=joined)
                for uid, joined in attendees
                if uid in users
            ),
            ratings=tuple(ratings),
        )

    async def _require(self, team_id: str, meeting_id: str) -> Meeting:
        meeting = await self._meetings.get(team_id, meeting_id)
        if meeting is None:
            raise MeetingNotFoundError()
        return meeting

    async def _require_active(self, team_id: str, meeting_id: str) -> Meeting:
        meeting = await self._require(team_id, meeting_id)
        if not meeting.is_active:
            raise MeetingEndedError()
        return meeting

    @staticmethod
    def _require_facilitator(meeting: Meeting, access: TeamAccess) -> None:
        if meeting.facilitator_id != access.user.id:
            raise NotFacilitatorError()

    async def _commit(self, team_id: str, meeting_id: str) -> None:
        await self._events.publish(
            TeamEvent(team_id, frozenset({Topic.MEETING}), meeting_id=meeting_id)
        )
        await self._uow.commit()
