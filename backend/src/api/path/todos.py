from fastapi import APIRouter

from src.api.schemas.common import PROBLEM_RESPONSES, IdPath
from src.api.schemas.todo import TodoListResponse, TodoResponse
from src.config.dependency import CalendarDep, ReadTeam, TodoServiceDep, WriteTeam

router = APIRouter(prefix="/teams/{team_id}/todos", tags=["todos"], responses=PROBLEM_RESPONSES)


@router.get("", summary="To-Dos with overdue flags and last closed week's completion rate")
async def list_todos(access: ReadTeam, cal: CalendarDep, todos: TodoServiceDep) -> TodoListResponse:
    return TodoListResponse.from_domain(await todos.list_for_team(access.team.id, cal))


@router.put("/{todo_id}/done", summary="Mark done (idempotent)")
async def mark_done(
    todo_id: IdPath, access: WriteTeam, cal: CalendarDep, todos: TodoServiceDep
) -> TodoResponse:
    return TodoResponse.from_domain(await todos.set_done(access, todo_id, True, cal))


@router.delete("/{todo_id}/done", summary="Undo done (idempotent)")
async def undo_done(
    todo_id: IdPath, access: WriteTeam, cal: CalendarDep, todos: TodoServiceDep
) -> TodoResponse:
    return TodoResponse.from_domain(await todos.set_done(access, todo_id, False, cal))
