from collections.abc import Sequence
from datetime import date

from src.domain.modules.issue.entity import Issue, IssueView
from src.domain.modules.issue.exceptions import IssueAlreadySolvedError, IssueNotFoundError
from src.domain.modules.issue.repository import IssueRepository
from src.domain.modules.meeting.repository import MeetingRepository
from src.domain.modules.scorecard.entity import MeasurableStatus, issue_title
from src.domain.modules.scorecard.exceptions import MeasurableNotFoundError, NotOffTrackError
from src.domain.modules.scorecard.repository import ScorecardRepository
from src.domain.modules.scorecard.service import cell_status, validate_week
from src.domain.modules.team.entity import TeamAccess
from src.domain.modules.user.entity import UNKNOWN_USER_NAME
from src.domain.modules.user.repository import UserRepository
from src.domain.shared.calendar import CalendarContext
from src.domain.shared.events import EventPublisher, TeamEvent, Topic
from src.domain.shared.unit_of_work import UnitOfWork

ISSUES_CHANGED = frozenset({Topic.ISSUES})


class IssueService:
    def __init__(
        self,
        issues: IssueRepository,
        scorecard: ScorecardRepository,
        meetings: MeetingRepository,
        users: UserRepository,
        uow: UnitOfWork,
        events: EventPublisher,
    ) -> None:
        self._issues = issues
        self._scorecard = scorecard
        self._meetings = meetings
        self._users = users
        self._uow = uow
        self._events = events

    # ------------------------------------------------------------------ reads

    async def list_open(self, team_id: str) -> list[IssueView]:
        return await self._views(team_id, await self._issues.list_open(team_id))

    async def list_solved(self, team_id: str) -> list[IssueView]:
        return await self._views(team_id, await self._issues.list_solved(team_id))

    async def get(self, team_id: str, issue_id: str) -> IssueView:
        return (await self._views(team_id, [await self._require(team_id, issue_id)]))[0]

    async def open_measurable_issue_ids(self, team_id: str) -> dict[tuple[str, date], str]:
        return await self._issues.open_measurable_issue_ids(team_id)

    # ------------------------------------------------------------------ writes

    async def create(
        self, access: TeamAccess, title: str, priority: int | None, cal: CalendarContext
    ) -> IssueView:
        issue = await self._issues.add(access.team.id, access.user.id, title, priority, cal.now)
        await self._commit(access.team.id)
        return await self.get(access.team.id, issue.id)

    async def set_priority(
        self, access: TeamAccess, issue_id: str, priority: int | None
    ) -> IssueView:
        issue = await self._require(access.team.id, issue_id)
        if issue.solved_at is not None:
            raise IssueAlreadySolvedError()
        await self._issues.set_priority(access.team.id, issue_id, priority)
        await self._commit(access.team.id)
        return await self.get(access.team.id, issue_id)

    async def solve(
        self, access: TeamAccess, issue_id: str, note: str, cal: CalendarContext
    ) -> IssueView:
        await self._require(access.team.id, issue_id)
        meeting = await self._meetings.get_active(access.team.id)
        solved = await self._issues.solve(
            access.team.id, issue_id, note, cal.now, meeting.id if meeting else None
        )
        if solved is None:  # conditional update lost: already solved (possibly concurrently)
            raise IssueAlreadySolvedError()
        await self._commit(access.team.id)
        return await self.get(access.team.id, issue_id)

    async def raise_from_measurable(
        self, access: TeamAccess, measurable_id: str, week_start: date, cal: CalendarContext
    ) -> tuple[IssueView, bool]:
        """Make it an Issue. Returns (issue, created); duplicate-free under concurrency."""
        measurable = await self._scorecard.get_measurable(access.team.id, measurable_id)
        if measurable is None:
            raise MeasurableNotFoundError()
        validate_week(week_start, cal)
        if await cell_status(self._scorecard, measurable, week_start, cal) is not (
            MeasurableStatus.OFF_TRACK
        ):
            raise NotOffTrackError()
        issue, created = await self._issues.add_from_measurable_or_get(
            team_id=access.team.id,
            owner_id=access.user.id,
            title=issue_title(measurable.name, week_start),
            created_at=cal.now,
            measurable_id=measurable_id,
            week_start=week_start,
        )
        if created:
            await self._events.publish(
                TeamEvent(access.team.id, frozenset({Topic.ISSUES, Topic.SCORECARD}))
            )
        await self._uow.commit()
        return await self.get(access.team.id, issue.id), created

    # ------------------------------------------------------------------ helpers

    async def _require(self, team_id: str, issue_id: str) -> Issue:
        issue = await self._issues.get(team_id, issue_id)
        if issue is None:
            raise IssueNotFoundError()
        return issue

    async def _commit(self, team_id: str) -> None:
        await self._events.publish(TeamEvent(team_id, ISSUES_CHANGED))
        await self._uow.commit()

    async def _views(self, team_id: str, issues: Sequence[Issue]) -> list[IssueView]:
        owners = await self._users.get_many(i.owner_id for i in issues)
        measurables = {m.id: m.name for m in await self._scorecard.list_measurables(team_id)}
        return [
            IssueView(
                issue=i,
                owner_name=owners[i.owner_id].name if i.owner_id in owners else UNKNOWN_USER_NAME,
                source_measurable_name=(
                    measurables.get(i.source.measurable_id)
                    if i.source and i.source.measurable_id
                    else None
                ),
            )
            for i in issues
        ]
