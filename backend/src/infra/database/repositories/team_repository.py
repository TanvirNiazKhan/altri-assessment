from collections.abc import Sequence

from sqlalchemy import exists, select

from src.domain.modules.team.entity import Team
from src.domain.modules.team.repository import TeamRepository
from src.domain.modules.user.entity import User
from src.infra.database.models import MembershipModel, TeamModel, UserModel
from src.infra.database.repositories.base import SqlRepository
from src.infra.database.repositories.mappers import to_team, to_user


class SqlTeamRepository(SqlRepository, TeamRepository):
    async def get(self, team_id: str) -> Team | None:
        m = await self._s.get(TeamModel, team_id)
        return to_team(m) if m else None

    async def list_by_company(self, company_id: str) -> Sequence[Team]:
        stmt = (
            select(TeamModel)
            .where(TeamModel.company_id == company_id)
            .order_by(TeamModel.name, TeamModel.id)
        )
        return [to_team(m) for m in await self._s.scalars(stmt)]

    async def list_for_user(self, user_id: str) -> Sequence[Team]:
        stmt = (
            select(TeamModel)
            .join(MembershipModel, MembershipModel.team_id == TeamModel.id)
            .where(MembershipModel.user_id == user_id)
            .order_by(TeamModel.name, TeamModel.id)
        )
        return [to_team(m) for m in await self._s.scalars(stmt)]

    async def is_member(self, user_id: str, team_id: str) -> bool:
        stmt = select(
            exists().where(MembershipModel.user_id == user_id, MembershipModel.team_id == team_id)
        )
        return bool(await self._s.scalar(stmt))

    async def list_members(self, team_id: str) -> Sequence[User]:
        stmt = (
            select(UserModel)
            .join(MembershipModel, MembershipModel.user_id == UserModel.id)
            .where(MembershipModel.team_id == team_id)
            .order_by(UserModel.name, UserModel.id)
        )
        return [to_user(m) for m in await self._s.scalars(stmt)]
