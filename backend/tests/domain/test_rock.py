from datetime import date

import pytest

from src.domain.modules.rock.entity import Milestone, Rock, RockStatus

TODAY = date(2026, 11, 11)


def rock(seeded: RockStatus, *milestones: tuple[date, bool]) -> Rock:
    ms = tuple(Milestone(f"ms{i}", "r", "m", d, done) for i, (d, done) in enumerate(milestones))
    return Rock("r", "tm", "u", "x", "2026-Q4", seeded_status=seeded, milestones=ms)


def test_status_milestone_due_today_vs_yesterday() -> None:
    assert rock(RockStatus.ON_TRACK, (TODAY, False)).status(TODAY) is RockStatus.ON_TRACK
    assert (
        rock(RockStatus.ON_TRACK, (date(2026, 11, 10), False)).status(TODAY) is RockStatus.OFF_TRACK
    )


def test_complete_and_seeded_off_track_win() -> None:
    assert (
        rock(RockStatus.COMPLETE, (date(2026, 11, 10), False)).status(TODAY) is RockStatus.COMPLETE
    )
    assert rock(RockStatus.OFF_TRACK).status(TODAY) is RockStatus.OFF_TRACK


@pytest.mark.parametrize(
    ("seeded", "done_flags", "expected"),
    [
        (RockStatus.ON_TRACK, [True, False, False], 33),
        (RockStatus.ON_TRACK, [True] + [False] * 7, 13),  # 12.5 -> 13, half up
        (RockStatus.COMPLETE, [], 100),
        (RockStatus.OFF_TRACK, [], 0),
        (RockStatus.ON_TRACK, [False], 0),
    ],
)
def test_progress(seeded: RockStatus, done_flags: list[bool], expected: int) -> None:
    assert rock(seeded, *[(TODAY, f) for f in done_flags]).progress_percent() == expected
