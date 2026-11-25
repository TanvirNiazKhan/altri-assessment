"""Clock port. Implementations live in src.infra.services.clock."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Current instant, timezone-aware UTC."""
        ...
