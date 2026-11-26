from datetime import date

from fastapi import APIRouter, Response, status

from src.api.schemas.common import PROBLEM_RESPONSES, IdPath
from src.api.schemas.issue import IssueResponse
from src.api.schemas.scorecard import ScorecardResponse, ScoreCellResponse, ScoreUpdateRequest
from src.config.dependency import (
    CalendarDep,
    IssueServiceDep,
    ReadTeam,
    ScorecardServiceDep,
    WriteTeam,
)

router = APIRouter(
    prefix="/teams/{team_id}/scorecard", tags=["scorecard"], responses=PROBLEM_RESPONSES
)


@router.get("", summary="Measurables by week: the last 13 weeks including the current one")
async def get_scorecard(
    access: ReadTeam, cal: CalendarDep, scorecard: ScorecardServiceDep, issues: IssueServiceDep
) -> ScorecardResponse:
    open_issues = await issues.open_measurable_issue_ids(access.team.id)
    return ScorecardResponse.from_domain(await scorecard.get(access.team.id, cal, open_issues))


@router.put(
    "/measurables/{measurable_id}/weeks/{week_start}",
    summary="Set or clear a score (last save wins)",
)
async def put_score(
    measurable_id: IdPath,
    week_start: date,
    body: ScoreUpdateRequest,
    access: WriteTeam,
    cal: CalendarDep,
    scorecard: ScorecardServiceDep,
) -> ScoreCellResponse:
    cell = await scorecard.set_score(access, measurable_id, week_start, body.value, cal)
    return ScoreCellResponse.from_domain(cell)


@router.post(
    "/measurables/{measurable_id}/weeks/{week_start}/issue",
    summary="Make it an Issue",
    description=(
        "Creates an Issue for an off-track cell, owned by the caller (201), or returns the "
        "existing unsolved Issue for that Measurable and week (200). Duplicate-free under "
        "concurrent requests."
    ),
    status_code=status.HTTP_201_CREATED,
    responses={200: {"model": IssueResponse, "description": "Existing unsolved Issue"}},
)
async def make_it_an_issue(
    measurable_id: IdPath,
    week_start: date,
    response: Response,
    access: WriteTeam,
    cal: CalendarDep,
    issues: IssueServiceDep,
) -> IssueResponse:
    issue, created = await issues.raise_from_measurable(access, measurable_id, week_start, cal)
    if not created:
        response.status_code = status.HTTP_200_OK
    return IssueResponse.from_domain(issue)
