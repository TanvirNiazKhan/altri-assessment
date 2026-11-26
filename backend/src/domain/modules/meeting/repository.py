"""Meeting repository interface (port). Implemented in src.infra.database.repositories."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

from src.domain.modules.meeting.entity import Meeting, MeetingSection, Rating
from src.domain.modules.meeting.summary import MeetingSummary


class MeetingRepository(ABC):
    @abstractmethod
    async def get_active(self, team_id: str) -> Meeting | None: ...

    @abstractmethod
    async def get(self, team_id: str, meeting_id: str) -> Meeting | None: ...

    @abstractmethod
    async def list_ended(self, team_id: str) -> Sequence[Meeting]:
        """Ended meetings, most recent first."""

    @abstractmethod
    async def create(self, team_id: str, facilitator_id: str, now: datetime) -> Meeting:
        """Fails with a ConflictError if the team already has an active meeting."""

    @abstractmethod
    async def add_attendee(self, meeting_id: str, user_id: str, joined_at: datetime) -> bool:
        """Idempotent. True if the user was newly added."""

    @abstractmethod
    async def list_attendees(self, meeting_id: str) -> Sequence[tuple[str, datetime]]:
        """(user_id, joined_at) in join order."""

    @abstractmethod
    async def advance(
        self,
        team_id: str,
        meeting_id: str,
        *,
        facilitator_id: str,
        expected: MeetingSection,
        to: MeetingSection,
        now: datetime,
    ) -> Meeting | None:
        """Conditional update; None if the meeting is not in `expected` (or ended)."""

    @abstractmethod
    async def end(
        self, team_id: str, meeting_id: str, *, facilitator_id: str, now: datetime
    ) -> Meeting | None:
        """Conditional update; None if already ended."""

    @abstractmethod
    async def upsert_rating(
        self, meeting_id: str, user_id: str, rating: int, now: datetime
    ) -> None: ...

    @abstractmethod
    async def list_ratings(self, meeting_id: str) -> Sequence[Rating]: ...

    @abstractmethod
    async def save_summary(self, summary: MeetingSummary, computed_at: datetime) -> None: ...

    @abstractmethod
    async def get_summary(self, meeting_id: str) -> MeetingSummary | None: ...
