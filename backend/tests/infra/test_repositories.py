"""SQL repositories against the seeded Postgres (read-only)."""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import build_engine, build_sessionmaker
from src.config.settings import Settings
from src.domain.modules.user.entity import Role
from src.infra.database.repositories import (
    SqlCompanyRepository,
    SqlTeamRepository,
    SqlUserRepository,
)

pytestmark = pytest.mark.db


@pytest.fixture
async def session(settings: Settings) -> AsyncIterator[AsyncSession]:
    engine = build_engine(settings)
    async with build_sessionmaker(engine)() as s:
        yield s
    await engine.dispose()


async def test_user_repository_maps_to_entity(session: AsyncSession) -> None:
    user = await SqlUserRepository(session).get("u5")
    assert user is not None and user.role is Role.OBSERVER and user.is_read_only


async def test_team_membership_queries(session: AsyncSession) -> None:
    repo = SqlTeamRepository(session)
    assert await repo.is_member("u2", "team_sales")
    assert not await repo.is_member("u2", "team_ops")
    assert [t.id for t in await repo.list_for_user("u2")] == ["team_lead", "team_sales"]
    assert {u.id for u in await repo.list_members("team_ops")} == {"u4", "u8", "u9"}


async def test_company_timezone(session: AsyncSession) -> None:
    company = await SqlCompanyRepository(session).get("co_1")
    assert company is not None and company.zone.key == "America/Chicago"
