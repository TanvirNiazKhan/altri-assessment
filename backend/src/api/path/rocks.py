from fastapi import APIRouter

from src.api.schemas.common import PROBLEM_RESPONSES
from src.api.schemas.rock import RockResponse
from src.config.dependency import CalendarDep, ReadTeam, RockServiceDep

router = APIRouter(prefix="/teams/{team_id}/rocks", tags=["rocks"], responses=PROBLEM_RESPONSES)


@router.get("", summary="Current quarter's Rocks with computed status, progress and Milestones")
async def list_rocks(
    access: ReadTeam, cal: CalendarDep, rocks: RockServiceDep
) -> list[RockResponse]:
    return [
        RockResponse.from_domain(v) for v in await rocks.list_current_quarter(access.team.id, cal)
    ]
