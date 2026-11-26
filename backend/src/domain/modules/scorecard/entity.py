"""Measurables (weekly metrics with a goal) and their scores."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum


class GoalType(StrEnum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"
    BETWEEN = "between"
    EXACTLY = "exactly"


class MeasurableStatus(StrEnum):
    ON_TRACK = "on_track"
    OFF_TRACK = "off_track"
    PENDING = "pending"


def _req(x: Decimal | None, name: str) -> Decimal:
    if x is None:
        raise ValueError(f"goal.{name} is required for this goal type")
    return x


@dataclass(frozen=True, slots=True)
class Goal:
    type: GoalType
    value: Decimal | None = None
    min: Decimal | None = None
    max: Decimal | None = None

    def is_met_by(self, score: Decimal) -> bool:
        match self.type:
            case GoalType.AT_LEAST:
                return score >= _req(self.value, "value")
            case GoalType.AT_MOST:
                return score <= _req(self.value, "value")
            case GoalType.EXACTLY:
                return score == _req(self.value, "value")
            case GoalType.BETWEEN:
                return _req(self.min, "min") <= score <= _req(self.max, "max")


@dataclass(frozen=True, slots=True)
class Measurable:
    id: str
    team_id: str
    owner_id: str
    name: str
    unit: str
    goal: Goal

    def status_for(
        self, score: Decimal | None, *, week_start: date, current_week: date
    ) -> MeasurableStatus:
        return measurable_status(self.goal, score, week_start=week_start, current_week=current_week)


@dataclass(frozen=True, slots=True)
class Score:
    measurable_id: str
    week_start: date
    value: Decimal
    updated_at: datetime | None = None
    updated_by: str | None = None
    version: int = 1


def measurable_status(
    goal: Goal, score: Decimal | None, *, week_start: date, current_week: date
) -> MeasurableStatus:
    """Missing score: off_track once the week has closed, pending while it is current."""
    if score is None:
        closed = week_start < current_week
        return MeasurableStatus.OFF_TRACK if closed else MeasurableStatus.PENDING
    return MeasurableStatus.ON_TRACK if goal.is_met_by(score) else MeasurableStatus.OFF_TRACK


SCORECARD_WEEKS = 13


def issue_title(measurable_name: str, week_start: date) -> str:
    """Title used by Make it an Issue, matching the seed ("New deals closed, week of Nov 2")."""
    return f"{measurable_name}, week of {week_start:%b} {week_start.day}"


@dataclass(frozen=True, slots=True)
class ScoreCell:
    week_start: date
    value: Decimal | None
    status: MeasurableStatus
    open_issue_id: str | None = None


@dataclass(frozen=True, slots=True)
class ScorecardRow:
    measurable: Measurable
    owner_name: str
    cells: tuple[ScoreCell, ...]


@dataclass(frozen=True, slots=True)
class Scorecard:
    weeks: tuple[date, ...]
    current_week: date
    rows: tuple[ScorecardRow, ...]
