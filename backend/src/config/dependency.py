"""Dependency injection: the only place that wires infra implementations to domain ports.

`build_*` functions assemble a service from one session; FastAPI dependencies, the
WebSocket dispatcher, the seed and the CLI all use them, so wiring exists once.
Routers declare what they need with the `Annotated` aliases; every team-scoped route
takes `ReadTeam` or `WriteTeam`, so access checks are uniform.
"""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Settings
from src.domain.modules.company.service import CompanyService
from src.domain.modules.issue.service import IssueService
from src.domain.modules.meeting.service import MeetingService
from src.domain.modules.report.service import RulesReportService
from src.domain.modules.rock.service import RockService
from src.domain.modules.scorecard.service import ScorecardService
from src.domain.modules.team.entity import TeamAccess
from src.domain.modules.team.service import TeamService
from src.domain.modules.todo.service import TodoService
from src.domain.modules.user.entity import User
from src.domain.modules.user.service import UserService
from src.domain.shared.calendar import CalendarContext
from src.domain.shared.clock import Clock
from src.domain.shared.events import EventPublisher
from src.infra.adapters.session_signer import SessionSigner
from src.infra.database.repositories import (
    SqlCompanyRepository,
    SqlIssueRepository,
    SqlMeetingRepository,
    SqlRockRepository,
    SqlScorecardRepository,
    SqlTeamRepository,
    SqlTodoRepository,
    SqlUserRepository,
)
from src.infra.database.unit_of_work import SqlUnitOfWork
from src.infra.realtime.publisher import PgEventPublisher

# ----------------------------------------------------------------- builders (no FastAPI)


def build_user_service(session: AsyncSession) -> UserService:
    return UserService(SqlUserRepository(session))


def build_team_service(session: AsyncSession) -> TeamService:
    return TeamService(SqlTeamRepository(session))


def build_company_service(session: AsyncSession, clock: Clock) -> CompanyService:
    return CompanyService(SqlCompanyRepository(session), clock)


def build_scorecard_service(session: AsyncSession, events: EventPublisher) -> ScorecardService:
    return ScorecardService(
        SqlScorecardRepository(session), SqlUserRepository(session), SqlUnitOfWork(session), events
    )


def build_issue_service(session: AsyncSession, events: EventPublisher) -> IssueService:
    return IssueService(
        SqlIssueRepository(session),
        SqlScorecardRepository(session),
        SqlMeetingRepository(session),
        SqlUserRepository(session),
        SqlUnitOfWork(session),
        events,
    )


def build_todo_service(session: AsyncSession, events: EventPublisher) -> TodoService:
    return TodoService(
        SqlTodoRepository(session),
        SqlIssueRepository(session),
        SqlMeetingRepository(session),
        build_team_service(session),
        SqlUserRepository(session),
        SqlUnitOfWork(session),
        events,
    )


def build_rock_service(session: AsyncSession) -> RockService:
    return RockService(SqlRockRepository(session), SqlUserRepository(session))


def build_meeting_service(session: AsyncSession, events: EventPublisher) -> MeetingService:
    return MeetingService(
        SqlMeetingRepository(session),
        SqlScorecardRepository(session),
        SqlIssueRepository(session),
        SqlTodoRepository(session),
        SqlUserRepository(session),
        SqlUnitOfWork(session),
        events,
    )


def build_rules_report_service(session: AsyncSession, events: EventPublisher) -> RulesReportService:
    return RulesReportService(
        SqlTeamRepository(session),
        SqlScorecardRepository(session),
        SqlTodoRepository(session),
        SqlRockRepository(session),
        SqlIssueRepository(session),
        SqlMeetingRepository(session),
        build_meeting_service(session, events),
    )


# ----------------------------------------------------------------- app-scoped singletons


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_clock(request: Request) -> Clock:
    clock: Clock = request.app.state.clock
    return clock


def get_session_signer(request: Request) -> SessionSigner:
    signer: SessionSigner = request.app.state.session_signer
    return signer


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One session per request. Write use cases commit explicitly; the rest rolls back."""
    async with request.app.state.sessionmaker() as session:
        yield session


SettingsDep = Annotated[Settings, Depends(get_settings)]
ClockDep = Annotated[Clock, Depends(get_clock)]
SessionSignerDep = Annotated[SessionSigner, Depends(get_session_signer)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_event_publisher(session: DbSessionDep) -> EventPublisher:
    return PgEventPublisher(session)


EventsDep = Annotated[EventPublisher, Depends(get_event_publisher)]

# ----------------------------------------------------------------- domain services


def get_user_service(session: DbSessionDep) -> UserService:
    return build_user_service(session)


def get_team_service(session: DbSessionDep) -> TeamService:
    return build_team_service(session)


def get_company_service(session: DbSessionDep, clock: ClockDep) -> CompanyService:
    return build_company_service(session, clock)


def get_scorecard_service(session: DbSessionDep, events: EventsDep) -> ScorecardService:
    return build_scorecard_service(session, events)


def get_issue_service(session: DbSessionDep, events: EventsDep) -> IssueService:
    return build_issue_service(session, events)


def get_todo_service(session: DbSessionDep, events: EventsDep) -> TodoService:
    return build_todo_service(session, events)


def get_rock_service(session: DbSessionDep) -> RockService:
    return build_rock_service(session)


def get_meeting_service(session: DbSessionDep, events: EventsDep) -> MeetingService:
    return build_meeting_service(session, events)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
TeamServiceDep = Annotated[TeamService, Depends(get_team_service)]
CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]
ScorecardServiceDep = Annotated[ScorecardService, Depends(get_scorecard_service)]
IssueServiceDep = Annotated[IssueService, Depends(get_issue_service)]
TodoServiceDep = Annotated[TodoService, Depends(get_todo_service)]
RockServiceDep = Annotated[RockService, Depends(get_rock_service)]
MeetingServiceDep = Annotated[MeetingService, Depends(get_meeting_service)]

# ----------------------------------------------------------------- request context


async def get_current_user(
    request: Request, users: UserServiceDep, signer: SessionSignerDep, settings: SettingsDep
) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    return await users.resolve_session_user(signer.unsign(token))


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_calendar(user: CurrentUser, companies: CompanyServiceDep) -> CalendarContext:
    return await companies.calendar_for(user)


CalendarDep = Annotated[CalendarContext, Depends(get_calendar)]


def require_team(*, write: bool) -> Callable[..., Awaitable[TeamAccess]]:
    async def dependency(team_id: str, user: CurrentUser, teams: TeamServiceDep) -> TeamAccess:
        return await teams.authorize(user, team_id, write=write)

    return dependency


ReadTeam = Annotated[TeamAccess, Depends(require_team(write=False))]
WriteTeam = Annotated[TeamAccess, Depends(require_team(write=True))]
