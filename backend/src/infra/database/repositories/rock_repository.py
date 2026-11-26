from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.domain.modules.rock.entity import Rock
from src.domain.modules.rock.repository import RockRepository
from src.infra.database.models import RockModel
from src.infra.database.repositories.base import SqlRepository
from src.infra.database.repositories.mappers import to_rock


class SqlRockRepository(SqlRepository, RockRepository):
    async def list_for_quarter(self, team_id: str, quarter: str) -> Sequence[Rock]:
        stmt = (
            select(RockModel)
            .where(RockModel.team_id == team_id, RockModel.quarter == quarter)
            .options(selectinload(RockModel.milestones))
            .order_by(RockModel.id)
        )
        return [to_rock(m) for m in await self._s.scalars(stmt)]
