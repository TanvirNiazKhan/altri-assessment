from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from src.domain.modules.scorecard.entity import (
    SCORECARD_WEEKS,
    Measurable,
    MeasurableStatus,
    Scorecard,
    ScorecardRow,
    ScoreCell,
)
from src.domain.modules.scorecard.exceptions import InvalidWeekError, MeasurableNotFoundError
from src.domain.modules.scorecard.repository import ScorecardRepository
from src.domain.modules.team.entity import TeamAccess
from src.domain.modules.user.entity import UNKNOWN_USER_NAME
from src.domain.modules.user.repository import UserRepository
from src.domain.shared.calendar import CalendarContext, week_window
from src.domain.shared.events import EventPublisher, TeamEvent, Topic
from src.domain.shared.unit_of_work import UnitOfWork


def validate_week(week_start: date, cal: CalendarContext) -> None:
    window = week_window(cal.current_week, SCORECARD_WEEKS)
    if week_start not in window:
        raise InvalidWeekError()


async def cell_status(
    scorecard: ScorecardRepository, measurable: Measurable, week_start: date, cal: CalendarContext
) -> MeasurableStatus:
    score = await scorecard.get_score(measurable.id, week_start)
    return measurable.status_for(
        score.value if score else None, week_start=week_start, current_week=cal.current_week
    )


async def statuses_for_week(
    scorecard: ScorecardRepository, team_id: str, week_start: date, current_week: date
) -> Sequence[tuple[Measurable, Decimal | None, MeasurableStatus]]:
    """Every Measurable of the team with its score and status for one week."""
    measurables = await scorecard.list_measurables(team_id)
    scores = await scorecard.list_scores([m.id for m in measurables], week_start, week_start)
    values = {s.measurable_id: s.value for s in scores}
    return [
        (
            m,
            values.get(m.id),
            m.status_for(values.get(m.id), week_start=week_start, current_week=current_week),
        )
        for m in measurables
    ]


class ScorecardService:
    def __init__(
        self,
        scorecard: ScorecardRepository,
        users: UserRepository,
        uow: UnitOfWork,
        events: EventPublisher,
    ) -> None:
        self._scorecard = scorecard
        self._users = users
        self._uow = uow
        self._events = events

    async def get(
        self,
        team_id: str,
        cal: CalendarContext,
        open_issues: Mapping[tuple[str, date], str],
        weeks: int = SCORECARD_WEEKS,
    ) -> Scorecard:
        window = week_window(cal.current_week, weeks)
        measurables = await self._scorecard.list_measurables(team_id)
        scores = await self._scorecard.list_scores(
            [m.id for m in measurables], window[0], window[-1]
        )
        by_cell = {(s.measurable_id, s.week_start): s.value for s in scores}
        owners = await self._users.get_many(m.owner_id for m in measurables)
        rows = tuple(
            ScorecardRow(
                measurable=m,
                owner_name=owners[m.owner_id].name if m.owner_id in owners else UNKNOWN_USER_NAME,
                cells=tuple(
                    ScoreCell(
                        week_start=w,
                        value=by_cell.get((m.id, w)),
                        status=m.status_for(
                            by_cell.get((m.id, w)), week_start=w, current_week=cal.current_week
                        ),
                        open_issue_id=open_issues.get((m.id, w)),
                    )
                    for w in window
                ),
            )
            for m in measurables
        )
        return Scorecard(weeks=tuple(window), current_week=cal.current_week, rows=rows)

    async def set_score(
        self,
        access: TeamAccess,
        measurable_id: str,
        week_start: date,
        value: Decimal | None,
        cal: CalendarContext,
    ) -> ScoreCell:
        """Set or clear one cell. Last save wins."""
        measurable = await self._scorecard.get_measurable(access.team.id, measurable_id)
        if measurable is None:
            raise MeasurableNotFoundError()
        validate_week(week_start, cal)
        if value is None:
            await self._scorecard.delete_score(measurable_id, week_start)
        else:
            await self._scorecard.upsert_score(
                measurable_id, week_start, value, updated_at=cal.now, updated_by=access.user.id
            )
        await self._events.publish(TeamEvent(access.team.id, frozenset({Topic.SCORECARD})))
        await self._uow.commit()
        return ScoreCell(
            week_start=week_start,
            value=value,
            status=measurable.status_for(
                value, week_start=week_start, current_week=cal.current_week
            ),
        )
