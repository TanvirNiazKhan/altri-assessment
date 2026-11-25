from dataclasses import dataclass
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class Company:
    id: str
    name: str
    timezone: str

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)
