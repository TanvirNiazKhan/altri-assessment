from collections.abc import Sequence
from datetime import timedelta

from src.domain.modules.issue.exceptions import IssueNotFoundError
from src.domain.modules.issue.repository import IssueRepository
from src.domain.modules.meeting.repository import MeetingRepository
from src.domain.modules.team.entity import TeamAccess
from src.domain.modules.team.service import TeamService
from src.domain.modules.todo.entity import (
    TODO_DUE_IN_DAYS,
    Todo,
    TodoList,
    TodoView,
    WeeklyCompletion,
    weekly_completion,
)
from src.domain.modules.todo.exceptions import TodoNotFoundError
from src.domain.modules.todo.repository import TodoRepository
from src.domain.modules.user.entity import UNKNOWN_USER_NAME
from src.domain.modules.user.repository import UserRepository
from src.domain.shared.calendar import CalendarContext, week_bounds_utc
from src.domain.shared.events import EventPublisher, TeamEvent, Topic
from src.domain.shared.unit_of_work import UnitOfWork


class TodoService:
    def __init__(
        self,
        todos: TodoRepository,
        issues: IssueRepository,
        meetings: MeetingRepository,
        teams: TeamService,
        users: UserRepository,
        uow: UnitOfWork,
        events: EventPublisher,
    ) -> None:
        self._todos = todos
        self._issues = issues
        self._meetings = meetings
        self._teams = teams
        self._users = users
        self._uow = uow
        self._events = events

    async def list_for_team(self, team_id: str, cal: CalendarContext) -> TodoList:
        todos = await self._todos.list(team_id)
        _, week_end = week_bounds_utc(cal.last_closed_week, cal.tz)
        return TodoList(
            items=tuple(await self.views(todos, cal)),
            last_closed_week=WeeklyCompletion(
                week_start=cal.last_closed_week,
                completion=weekly_completion(
                    todos, week_start=cal.last_closed_week, week_end_utc=week_end, now=cal.now
                ),
            ),
        )

    async def create_from_issue(
        self,
        access: TeamAccess,
        issue_id: str,
        title: str,
        owner_id: str,
        cal: CalendarContext,
    ) -> TodoView:
        if await self._issues.get(access.team.id, issue_id) is None:
            raise IssueNotFoundError()
        await self._teams.require_owner(access.team.id, owner_id)
        meeting = await self._meetings.get_active(access.team.id)
        todo = await self._todos.add(
            team_id=access.team.id,
            owner_id=owner_id,
            title=title,
            due_date=cal.today + timedelta(days=TODO_DUE_IN_DAYS),
            created_at=cal.now,
            source_issue_id=issue_id,
            created_in_meeting_id=meeting.id if meeting else None,
        )
        await self._commit(access.team.id)
        return (await self.views([todo], cal))[0]

    async def set_done(
        self, access: TeamAccess, todo_id: str, done: bool, cal: CalendarContext
    ) -> TodoView:
        """Idempotent: marking a done To-Do done keeps its original done time."""
        todo = await self._todos.get(access.team.id, todo_id)
        if todo is None:
            raise TodoNotFoundError()
        if done != (todo.done_at is not None):
            todo = await self._todos.set_done_at(access.team.id, todo_id, cal.now if done else None)
            await self._commit(access.team.id)
        return (await self.views([todo], cal))[0]

    async def views(self, todos: Sequence[Todo], cal: CalendarContext) -> list[TodoView]:
        owners = await self._users.get_many(t.owner_id for t in todos)
        titles = await self._todos.issue_titles(
            [t.source_issue_id for t in todos if t.source_issue_id]
        )
        return [
            TodoView(
                todo=t,
                owner_name=owners[t.owner_id].name if t.owner_id in owners else UNKNOWN_USER_NAME,
                overdue=t.is_overdue(today=cal.today, now=cal.now),
                source_issue_title=titles.get(t.source_issue_id) if t.source_issue_id else None,
            )
            for t in todos
        ]

    async def _commit(self, team_id: str) -> None:
        await self._events.publish(TeamEvent(team_id, frozenset({Topic.TODOS})))
        await self._uow.commit()
