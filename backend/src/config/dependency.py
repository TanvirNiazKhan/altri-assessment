"""Dependency injection: the only place that wires infra implementations to domain ports.

`build_*` functions assemble a service from one session. Routers declare what they need
with the `Annotated` aliases; every team-scoped route takes `ReadTeam` or `WriteTeam`,
so access checks are uniform.
"""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Settings
from src.domain.modules.company.service import CompanyService
from src.domain.modules.team.entity import TeamAccess
from src.domain.modules.team.service import TeamService
from src.domain.modules.user.entity import User
from src.domain.modules.user.service import UserService
from src.domain.shared.calendar import CalendarContext
from src.domain.shared.clock import Clock
from src.infra.adapters.session_signer import SessionSigner
from src.infra.database.repositories import (
    SqlCompanyRepository,
    SqlTeamRepository,
    SqlUserRepository,
)

# ----------------------------------------------------------------- builders (no FastAPI)


def build_user_service(session: AsyncSession) -> UserService:
    return UserService(SqlUserRepository(session))


def build_team_service(session: AsyncSession) -> TeamService:
    return TeamService(SqlTeamRepository(session))


def build_company_service(session: AsyncSession, clock: Clock) -> CompanyService:
    return CompanyService(SqlCompanyRepository(session), clock)


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

# ----------------------------------------------------------------- domain services


def get_user_service(session: DbSessionDep) -> UserService:
    return build_user_service(session)


def get_team_service(session: DbSessionDep) -> TeamService:
    return build_team_service(session)


def get_company_service(session: DbSessionDep, clock: ClockDep) -> CompanyService:
    return build_company_service(session, clock)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
TeamServiceDep = Annotated[TeamService, Depends(get_team_service)]
CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]

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
