from typing import Annotated

from fastapi import APIRouter, Query

from src.api.schemas.common import PROBLEM_RESPONSES
from src.api.schemas.team import TeamDetailResponse
from src.api.schemas.user import UserResponse
from src.config.dependency import ReadTeam, TeamServiceDep

router = APIRouter(prefix="/teams/{team_id}", tags=["teams"], responses=PROBLEM_RESPONSES)


@router.get("")
async def get_team(access: ReadTeam) -> TeamDetailResponse:
    return TeamDetailResponse.from_access(access)


@router.get("/members")
async def list_members(
    access: ReadTeam,
    teams: TeamServiceDep,
    can_own: Annotated[
        bool, Query(description="Only users who may own items (no Observers)")
    ] = False,
) -> list[UserResponse]:
    users = await teams.members(access.team.id, can_own_only=can_own)
    return [UserResponse.model_validate(u) for u in users]
