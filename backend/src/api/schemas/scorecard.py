from datetime import date
from decimal import Decimal

from pydantic import Field

from src.api.schemas.common import Number, RequestSchema, ResponseSchema, UserRefResponse
from src.domain.modules.scorecard.entity import (
    GoalType,
    MeasurableStatus,
    Scorecard,
    ScorecardRow,
    ScoreCell,
)


class GoalResponse(ResponseSchema):
    type: GoalType
    value: Number | None
    min: Number | None
    max: Number | None


class ScoreCellResponse(ResponseSchema):
    week_start: date
    value: Number | None
    status: MeasurableStatus
    open_issue_id: str | None = None

    @classmethod
    def from_domain(cls, c: ScoreCell) -> "ScoreCellResponse":
        return cls(
            week_start=c.week_start, value=c.value, status=c.status, open_issue_id=c.open_issue_id
        )


class ScorecardRowResponse(ResponseSchema):
    id: str
    name: str
    unit: str
    owner: UserRefResponse
    goal: GoalResponse
    cells: list[ScoreCellResponse]

    @classmethod
    def from_domain(cls, r: ScorecardRow) -> "ScorecardRowResponse":
        m = r.measurable
        return cls(
            id=m.id,
            name=m.name,
            unit=m.unit,
            owner=UserRefResponse(id=m.owner_id, name=r.owner_name),
            goal=GoalResponse(type=m.goal.type, value=m.goal.value, min=m.goal.min, max=m.goal.max),
            cells=[ScoreCellResponse.from_domain(c) for c in r.cells],
        )


class ScorecardResponse(ResponseSchema):
    weeks: list[date]
    current_week: date
    rows: list[ScorecardRowResponse]

    @classmethod
    def from_domain(cls, s: Scorecard) -> "ScorecardResponse":
        return cls(
            weeks=list(s.weeks),
            current_week=s.current_week,
            rows=[ScorecardRowResponse.from_domain(r) for r in s.rows],
        )


class ScoreUpdateRequest(RequestSchema):
    """`null` clears the score. Last save wins."""

    value: Decimal | None = Field(max_digits=14, decimal_places=4, allow_inf_nan=False)
