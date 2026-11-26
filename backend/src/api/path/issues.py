from enum import StrEnum

from fastapi import APIRouter, status

from src.api.schemas.common import PROBLEM_RESPONSES, IdPath
from src.api.schemas.issue import (
    IssueCreateRequest,
    IssuePriorityRequest,
    IssueResponse,
    IssueSolveRequest,
    IssueTodoCreateRequest,
)
from src.api.schemas.todo import TodoResponse
from src.config.dependency import (
    CalendarDep,
    IssueServiceDep,
    ReadTeam,
    TodoServiceDep,
    WriteTeam,
)

router = APIRouter(prefix="/teams/{team_id}/issues", tags=["issues"], responses=PROBLEM_RESPONSES)


class IssueStatusFilter(StrEnum):
    OPEN = "open"
    SOLVED = "solved"


@router.get("", summary="Open Issues in Issue order, or solved Issues (most recent first)")
async def list_issues(
    access: ReadTeam, issues: IssueServiceDep, status: IssueStatusFilter = IssueStatusFilter.OPEN
) -> list[IssueResponse]:
    views = (
        await issues.list_open(access.team.id)
        if status is IssueStatusFilter.OPEN
        else await issues.list_solved(access.team.id)
    )
    return [IssueResponse.from_domain(v) for v in views]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create an Issue (owner = caller)")
async def create_issue(
    body: IssueCreateRequest, access: WriteTeam, cal: CalendarDep, issues: IssueServiceDep
) -> IssueResponse:
    return IssueResponse.from_domain(await issues.create(access, body.title, body.priority, cal))


@router.get("/{issue_id}")
async def get_issue(issue_id: IdPath, access: ReadTeam, issues: IssueServiceDep) -> IssueResponse:
    return IssueResponse.from_domain(await issues.get(access.team.id, issue_id))


@router.patch("/{issue_id}", summary="Set or clear the priority")
async def set_priority(
    issue_id: IdPath, body: IssuePriorityRequest, access: WriteTeam, issues: IssueServiceDep
) -> IssueResponse:
    return IssueResponse.from_domain(await issues.set_priority(access, issue_id, body.priority))


@router.post("/{issue_id}/solve", summary="Solve with a required note")
async def solve_issue(
    issue_id: IdPath,
    body: IssueSolveRequest,
    access: WriteTeam,
    cal: CalendarDep,
    issues: IssueServiceDep,
) -> IssueResponse:
    return IssueResponse.from_domain(await issues.solve(access, issue_id, body.note, cal))


@router.post(
    "/{issue_id}/todos",
    status_code=status.HTTP_201_CREATED,
    summary="Add a To-Do linked to the Issue (due in 7 days)",
)
async def add_todo(
    issue_id: IdPath,
    body: IssueTodoCreateRequest,
    access: WriteTeam,
    cal: CalendarDep,
    todos: TodoServiceDep,
) -> TodoResponse:
    view = await todos.create_from_issue(access, issue_id, body.title, body.owner_id, cal)
    return TodoResponse.from_domain(view)
