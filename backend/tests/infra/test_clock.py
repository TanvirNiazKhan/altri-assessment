from datetime import UTC, datetime, timedelta, timezone

from src.infra.services.clock import FrozenClock, RunningClock, build_clock

ANCHOR = datetime(2026, 11, 11, 15, tzinfo=UTC)


def test_frozen_clock_is_fixed_and_advances_on_demand() -> None:
    c = FrozenClock(ANCHOR)
    assert c.now() == c.now() == ANCHOR
    c.advance(90)
    assert c.now() == ANCHOR + timedelta(seconds=90)


def test_running_clock_starts_at_anchor_and_moves_forward() -> None:
    c = RunningClock(ANCHOR)
    first = c.now()
    assert ANCHOR <= first < ANCHOR + timedelta(seconds=5)
    assert c.now() >= first


def test_clocks_normalise_to_utc() -> None:
    plus2 = ANCHOR.astimezone(timezone(timedelta(hours=2)))
    assert FrozenClock(plus2).now().tzinfo is UTC


def test_build_clock_by_mode() -> None:
    assert isinstance(build_clock(ANCHOR, "frozen"), FrozenClock)
    assert isinstance(build_clock(ANCHOR, "running"), RunningClock)
