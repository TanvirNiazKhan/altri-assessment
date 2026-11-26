from src.domain.modules.rock.entity import RockView
from src.domain.modules.rock.repository import RockRepository
from src.domain.modules.user.entity import UNKNOWN_USER_NAME
from src.domain.modules.user.repository import UserRepository
from src.domain.shared.calendar import CalendarContext


class RockService:
    """Rocks are seeded and read-only; status and progress are always computed."""

    def __init__(self, rocks: RockRepository, users: UserRepository) -> None:
        self._rocks = rocks
        self._users = users

    async def list_current_quarter(self, team_id: str, cal: CalendarContext) -> list[RockView]:
        rocks = await self._rocks.list_for_quarter(team_id, cal.quarter)
        owners = await self._users.get_many(r.owner_id for r in rocks)
        return [
            RockView(
                rock=r,
                owner_name=owners[r.owner_id].name if r.owner_id in owners else UNKNOWN_USER_NAME,
                status=r.status(cal.today),
                progress_percent=r.progress_percent(),
            )
            for r in rocks
        ]
