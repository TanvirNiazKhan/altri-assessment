from collections.abc import Sequence

from src.domain.modules.team.entity import Team, TeamAccess, can_read_team, can_write_team
from src.domain.modules.team.exceptions import (
    InvalidOwnerError,
    TeamNotFoundError,
    TeamReadOnlyError,
)
from src.domain.modules.team.repository import TeamRepository
from src.domain.modules.user.entity import User


class TeamService:
    def __init__(self, teams: TeamRepository) -> None:
        self._teams = teams

    async def accessible_teams(self, user: User) -> Sequence[Team]:
        if user.is_admin:
            return await self._teams.list_by_company(user.company_id)
        return await self._teams.list_for_user(user.id)

    async def authorize(self, user: User, team_id: str, *, write: bool) -> TeamAccess:
        team = await self._teams.get(team_id)
        if team is None:
            raise TeamNotFoundError()
        is_member = await self._teams.is_member(user.id, team.id)
        if not can_read_team(user, team, is_member=is_member):
            raise TeamNotFoundError()
        can_write = can_write_team(user, team, is_member=is_member)
        if write and not can_write:
            raise TeamReadOnlyError()
        return TeamAccess(user=user, team=team, can_write=can_write)

    async def members(self, team_id: str, *, can_own_only: bool = False) -> Sequence[User]:
        users = await self._teams.list_members(team_id)
        return [u for u in users if u.can_own_items] if can_own_only else users

    async def require_owner(self, team_id: str, user_id: str) -> User:
        """An owner is one of the team's Admins or Team Members (never an Observer)."""
        for user in await self.members(team_id, can_own_only=True):
            if user.id == user_id:
                return user
        raise InvalidOwnerError()
