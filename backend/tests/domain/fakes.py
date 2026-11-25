"""In-memory repository fakes: domain services are tested without a database."""

from collections.abc import Iterable, Sequence

from src.domain.modules.team.entity import Team
from src.domain.modules.team.repository import TeamRepository
from src.domain.modules.user.entity import Role, User
from src.domain.modules.user.repository import UserRepository

CO = "co_1"
ADMIN = User("u1", CO, "Avery", "a@x.test", Role.ADMIN)
MEMBER = User("u2", CO, "Blake", "b@x.test", Role.TEAM_MEMBER)
OBSERVER = User("u5", CO, "Eli", "e@x.test", Role.OBSERVER)
OUTSIDER = User("u9", "co_2", "Zed", "z@x.test", Role.ADMIN)
LEAD = Team("team_lead", CO, "Leadership")
SALES = Team("team_sales", CO, "Sales")


class FakeUserRepository(UserRepository):
    def __init__(self, users: Sequence[User]) -> None:
        self._users = {u.id: u for u in users}

    async def get(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    async def list_all(self) -> Sequence[User]:
        return sorted(self._users.values(), key=lambda u: (u.name, u.id))

    async def get_many(self, user_ids: Iterable[str]) -> dict[str, User]:
        return {uid: self._users[uid] for uid in user_ids if uid in self._users}


class FakeTeamRepository(TeamRepository):
    def __init__(self, teams: Sequence[Team], members: dict[str, list[User]] | None = None) -> None:
        self._teams = {t.id: t for t in teams}
        self._members = members or {}

    async def get(self, team_id: str) -> Team | None:
        return self._teams.get(team_id)

    async def list_by_company(self, company_id: str) -> Sequence[Team]:
        return [t for t in self._teams.values() if t.company_id == company_id]

    async def list_for_user(self, user_id: str) -> Sequence[Team]:
        return [
            self._teams[tid]
            for tid, users in self._members.items()
            if any(u.id == user_id for u in users)
        ]

    async def is_member(self, user_id: str, team_id: str) -> bool:
        return any(u.id == user_id for u in self._members.get(team_id, []))

    async def list_members(self, team_id: str) -> Sequence[User]:
        return self._members.get(team_id, [])
