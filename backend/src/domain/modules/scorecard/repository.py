"""Scorecard repository interface (port). Implemented in src.infra.database.repositories."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal

from src.domain.modules.scorecard.entity import Measurable, Score


class ScorecardRepository(ABC):
    @abstractmethod
    async def list_measurables(self, team_id: str) -> Sequence[Measurable]: ...

    @abstractmethod
    async def get_measurable(self, team_id: str, measurable_id: str) -> Measurable | None: ...

    @abstractmethod
    async def list_scores(
        self, measurable_ids: Sequence[str], first_week: date, last_week: date
    ) -> Sequence[Score]: ...

    @abstractmethod
    async def get_score(self, measurable_id: str, week_start: date) -> Score | None: ...

    @abstractmethod
    async def upsert_score(
        self,
        measurable_id: str,
        week_start: date,
        value: Decimal,
        *,
        updated_at: datetime,
        updated_by: str,
    ) -> Score: ...

    @abstractmethod
    async def delete_score(self, measurable_id: str, week_start: date) -> None: ...
