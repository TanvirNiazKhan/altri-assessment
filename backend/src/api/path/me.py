from fastapi import APIRouter

from src.api.schemas.common import PROBLEM_RESPONSES
from src.api.schemas.me import CalendarResponse, MeResponse
from src.api.schemas.team import TeamResponse
from src.api.schemas.user import UserResponse
from src.config.dependency import CalendarDep, CurrentUser, TeamServiceDep

router = APIRouter(tags=["me"], responses=PROBLEM_RESPONSES)


@router.get("/me", summary="Current user, accessible teams, server calendar")
async def me(user: CurrentUser, teams: TeamServiceDep, calendar: CalendarDep) -> MeResponse:
    return MeResponse(
        user=UserResponse.model_validate(user),
        teams=[TeamResponse.model_validate(t) for t in await teams.accessible_teams(user)],
        calendar=CalendarResponse.from_context(calendar),
    )
