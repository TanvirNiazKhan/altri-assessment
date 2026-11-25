"""Clock implementations (port: src.domain.shared.clock.Clock).

The only module allowed to read the system clock (enforced by ruff TID251).
"""

import time
from datetime import UTC, datetime, timedelta
from typing import Literal

from src.domain.shared.clock import Clock


class FrozenClock:
    """Fixed instant. Rules report and tests; `advance()` drives timer tests."""

    def __init__(self, at: datetime) -> None:
        self._at = at.astimezone(UTC)

    def now(self) -> datetime:
        return self._at

    def advance(self, seconds: float) -> None:
        self._at += timedelta(seconds=seconds)


class RunningClock:
    """`anchor` plus monotonic time since construction, so timers tick near APP_NOW."""

    def __init__(self, anchor: datetime) -> None:
        self._anchor = anchor.astimezone(UTC)
        self._t0 = time.monotonic()

    def now(self) -> datetime:
        return self._anchor + timedelta(seconds=time.monotonic() - self._t0)


def build_clock(anchor: datetime, mode: Literal["running", "frozen"]) -> Clock:
    return FrozenClock(anchor) if mode == "frozen" else RunningClock(anchor)
