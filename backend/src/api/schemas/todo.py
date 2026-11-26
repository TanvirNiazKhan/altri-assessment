from datetime import date, datetime

from src.api.schemas.common import ResponseSchema, UserRefResponse
from src.domain.modules.todo.entity import TodoList, TodoView


class TodoSourceIssueResponse(ResponseSchema):
    id: str
    title: str | None


class TodoResponse(ResponseSchema):
    id: str
    title: str
    owner: UserRefResponse
    due_date: date
    done_at: datetime | None
    overdue: bool
    created_at: datetime
    source_issue: TodoSourceIssueResponse | None
    created_in_meeting_id: str | None

    @classmethod
    def from_domain(cls, v: TodoView) -> "TodoResponse":
        t = v.todo
        return cls(
            id=t.id,
            title=t.title,
            owner=UserRefResponse(id=t.owner_id, name=v.owner_name),
            due_date=t.due_date,
            done_at=t.done_at,
            overdue=v.overdue,
            created_at=t.created_at,
            source_issue=TodoSourceIssueResponse(id=t.source_issue_id, title=v.source_issue_title)
            if t.source_issue_id
            else None,
            created_in_meeting_id=t.created_in_meeting_id,
        )


class CompletionResponse(ResponseSchema):
    due: int
    done: int
    rate_percent: int
    meets_target: bool


class WeeklyCompletionResponse(ResponseSchema):
    week_start: date
    completion: CompletionResponse | None
    target_percent: int = 90


class TodoListResponse(ResponseSchema):
    items: list[TodoResponse]
    last_closed_week: WeeklyCompletionResponse

    @classmethod
    def from_domain(cls, todo_list: TodoList) -> "TodoListResponse":
        c = todo_list.last_closed_week.completion
        return cls(
            items=[TodoResponse.from_domain(v) for v in todo_list.items],
            last_closed_week=WeeklyCompletionResponse(
                week_start=todo_list.last_closed_week.week_start,
                completion=CompletionResponse(
                    due=c.due, done=c.done, rate_percent=c.rate_percent, meets_target=c.meets_target
                )
                if c
                else None,
            ),
        )
