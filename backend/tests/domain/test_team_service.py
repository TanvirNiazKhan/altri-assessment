import pytest

from src.domain.modules.team.exceptions import TeamNotFoundError, TeamReadOnlyError
from src.domain.modules.team.service import TeamService
from tests.domain.fakes import (
    ADMIN,
    LEAD,
    MEMBER,
    OBSERVER,
    OUTSIDER,
    SALES,
    FakeTeamRepository,
)


@pytest.fixture
def service() -> TeamService:
    repo = FakeTeamRepository([LEAD, SALES], members={"team_lead": [MEMBER, OBSERVER]})
    return TeamService(repo)


async def test_member_reads_and_writes_own_team(service: TeamService) -> None:
    access = await service.authorize(MEMBER, "team_lead", write=True)
    assert access.can_write and access.team == LEAD


async def test_admin_reaches_any_team_in_company(service: TeamService) -> None:
    assert (await service.authorize(ADMIN, "team_sales", write=True)).can_write
    assert {t.id for t in await service.accessible_teams(ADMIN)} == {"team_lead", "team_sales"}


async def test_non_member_and_unknown_team_look_identical(service: TeamService) -> None:
    with pytest.raises(TeamNotFoundError):
        await service.authorize(MEMBER, "team_sales", write=False)
    with pytest.raises(TeamNotFoundError):
        await service.authorize(MEMBER, "nope", write=False)


async def test_admin_of_other_company_cannot_see_team(service: TeamService) -> None:
    with pytest.raises(TeamNotFoundError):
        await service.authorize(OUTSIDER, "team_lead", write=False)


async def test_observer_reads_but_cannot_write(service: TeamService) -> None:
    assert not (await service.authorize(OBSERVER, "team_lead", write=False)).can_write
    with pytest.raises(TeamReadOnlyError):
        await service.authorize(OBSERVER, "team_lead", write=True)


async def test_members_can_own_filter_drops_observers(service: TeamService) -> None:
    ids = [u.id for u in await service.members("team_lead", can_own_only=True)]
    assert ids == ["u2"]
