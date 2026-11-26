from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum

from src.domain.shared.numbers import round_half_up


class RockStatus(StrEnum):
    ON_TRACK = "on_track"
    OFF_TRACK = "off_track"
    COMPLETE = "complete"


@dataclass(frozen=True, slots=True)
class Milestone:
    id: str
    rock_id: str
    title: str
    due_date: date
    done: bool = False

    def is_past_due(self, today: date) -> bool:
        return not self.done and self.due_date < today


@dataclass(frozen=True, slots=True)
class Rock:
    id: str
    team_id: str
    owner_id: str
    title: str
    quarter: str
    seeded_status: RockStatus
    milestones: tuple[Milestone, ...] = field(default_factory=tuple)

    def status(self, today: date) -> RockStatus:
        if self.seeded_status is RockStatus.COMPLETE:
            return RockStatus.COMPLETE
        if self.seeded_status is RockStatus.OFF_TRACK or any(
            m.is_past_due(today) for m in self.milestones
        ):
            return RockStatus.OFF_TRACK
        return RockStatus.ON_TRACK

    def progress_percent(self) -> int:
        if not self.milestones:
            return 100 if self.seeded_status is RockStatus.COMPLETE else 0
        done = sum(1 for m in self.milestones if m.done)
        return int(round_half_up(Decimal(100 * done) / len(self.milestones)))


@dataclass(frozen=True, slots=True)
class RockView:
    rock: Rock
    owner_name: str
    status: RockStatus
    progress_percent: int
