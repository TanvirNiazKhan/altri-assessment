from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from src.domain.modules.scorecard.entity import Measurable, Score
from src.domain.modules.scorecard.repository import ScorecardRepository
from src.infra.database.errors import translate_db_errors
from src.infra.database.models import MeasurableModel, ScoreModel
from src.infra.database.repositories.base import SqlRepository
from src.infra.database.repositories.mappers import to_measurable, to_score


class SqlScorecardRepository(SqlRepository, ScorecardRepository):
    async def list_measurables(self, team_id: str) -> Sequence[Measurable]:
        stmt = (
            select(MeasurableModel)
            .where(MeasurableModel.team_id == team_id)
            .order_by(MeasurableModel.sort_order, MeasurableModel.id)
        )
        return [to_measurable(m) for m in await self._s.scalars(stmt)]

    async def get_measurable(self, team_id: str, measurable_id: str) -> Measurable | None:
        stmt = select(MeasurableModel).where(
            MeasurableModel.id == measurable_id, MeasurableModel.team_id == team_id
        )
        m = await self._s.scalar(stmt)
        return to_measurable(m) if m else None

    async def list_scores(
        self, measurable_ids: Sequence[str], first_week: date, last_week: date
    ) -> Sequence[Score]:
        if not measurable_ids:
            return []
        stmt = select(ScoreModel).where(
            ScoreModel.measurable_id.in_(measurable_ids),
            ScoreModel.week_start.between(first_week, last_week),
        )
        return [to_score(m) for m in await self._s.scalars(stmt)]

    async def get_score(self, measurable_id: str, week_start: date) -> Score | None:
        m = await self._s.get(ScoreModel, (measurable_id, week_start), populate_existing=True)
        return to_score(m) if m else None

    async def upsert_score(
        self,
        measurable_id: str,
        week_start: date,
        value: Decimal,
        *,
        updated_at: datetime,
        updated_by: str,
    ) -> Score:
        insert_stmt = insert(ScoreModel).values(
            measurable_id=measurable_id,
            week_start=week_start,
            value=value,
            updated_at=updated_at,
            updated_by=updated_by,
        )
        upsert = insert_stmt.on_conflict_do_update(
            index_elements=[ScoreModel.measurable_id, ScoreModel.week_start],
            set_={
                "value": insert_stmt.excluded.value,
                "updated_at": insert_stmt.excluded.updated_at,
                "updated_by": insert_stmt.excluded.updated_by,
                "version": ScoreModel.version + 1,
            },
        ).returning(ScoreModel)
        async with translate_db_errors():
            row = await self._s.scalar(
                select(ScoreModel).from_statement(upsert).execution_options(populate_existing=True)
            )
        assert row is not None
        return to_score(row)

    async def delete_score(self, measurable_id: str, week_start: date) -> None:
        await self._s.execute(
            delete(ScoreModel).where(
                ScoreModel.measurable_id == measurable_id, ScoreModel.week_start == week_start
            )
        )
