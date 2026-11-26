from datetime import date
from decimal import Decimal

import pytest

from src.domain.modules.scorecard.entity import Goal, GoalType, MeasurableStatus, measurable_status

D = Decimal
CURRENT_WEEK = date(2026, 11, 9)
CLOSED_WEEK = date(2026, 9, 7)
ON, OFF, PENDING = MeasurableStatus.ON_TRACK, MeasurableStatus.OFF_TRACK, MeasurableStatus.PENDING


@pytest.mark.parametrize(
    ("goal", "score", "expected"),
    [
        (Goal(GoalType.AT_LEAST, value=D(10)), D(10), ON),
        (Goal(GoalType.AT_LEAST, value=D(10)), D("9.99"), OFF),
        (Goal(GoalType.AT_MOST, value=D("3.0")), D("3.0"), ON),
        (Goal(GoalType.AT_MOST, value=D("3.0")), D("3.01"), OFF),
        (Goal(GoalType.BETWEEN, min=D(2), max=D(4)), D("2.0"), ON),
        (Goal(GoalType.BETWEEN, min=D(2), max=D(4)), D(4), ON),
        (Goal(GoalType.BETWEEN, min=D(2), max=D(4)), D("4.1"), OFF),
        (Goal(GoalType.EXACTLY, value=D(2)), D(0), OFF),
        (Goal(GoalType.EXACTLY, value=D(500)), D(500), ON),
    ],
)
def test_goal_edges(goal: Goal, score: D, expected: MeasurableStatus) -> None:
    status = measurable_status(goal, score, week_start=CLOSED_WEEK, current_week=CURRENT_WEEK)
    assert status is expected


def test_missing_score_off_track_when_closed_pending_when_current() -> None:
    g = Goal(GoalType.AT_LEAST, value=D(1))
    closed = measurable_status(g, None, week_start=date(2026, 11, 2), current_week=CURRENT_WEEK)
    current = measurable_status(g, None, week_start=CURRENT_WEEK, current_week=CURRENT_WEEK)
    assert (closed, current) == (OFF, PENDING)


def test_malformed_goal_raises() -> None:
    with pytest.raises(ValueError, match=r"goal\.value"):
        Goal(GoalType.AT_LEAST).is_met_by(D(1))
