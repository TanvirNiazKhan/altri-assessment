from datetime import date, datetime
from typing import Annotated

from pydantic import Field, StringConstraints

from src.api.schemas.common import EntityId, RequestSchema, ResponseSchema, UserRefResponse
from src.domain.modules.issue.entity import (
    ISSUE_TITLE_MAX,
    NOTE_MAX,
    PRIORITY_MAX,
    PRIORITY_MIN,
    IssueSourceType,
    IssueView,
)
from src.domain.modules.todo.entity import TODO_TITLE_MAX

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=ISSUE_TITLE_MAX)
]
Priority = Annotated[int, Field(ge=PRIORITY_MIN, le=PRIORITY_MAX)]


class IssueSourceResponse(ResponseSchema):
    type: IssueSourceType
    measurable_id: str | None = None
    measurable_name: str | None = None
    week_start: date | None = None
    rock_id: str | None = None


class IssueResponse(ResponseSchema):
    id: str
    title: str
    owner: UserRefResponse
    priority: int | None
    created_at: datetime
    solved_at: datetime | None
    resolution_note: str | None
    source: IssueSourceResponse | None
    solved_in_meeting_id: str | None

    @classmethod
    def from_domain(cls, v: IssueView) -> "IssueResponse":
        i = v.issue
        return cls(
            id=i.id,
            title=i.title,
            owner=UserRefResponse(id=i.owner_id, name=v.owner_name),
            priority=i.priority,
            created_at=i.created_at,
            solved_at=i.solved_at,
            resolution_note=i.resolution_note,
            source=IssueSourceResponse(
                type=i.source.type,
                measurable_id=i.source.measurable_id,
                measurable_name=v.source_measurable_name,
                week_start=i.source.week_start,
                rock_id=i.source.rock_id,
            )
            if i.source
            else None,
            solved_in_meeting_id=i.solved_in_meeting_id,
        )


class IssueCreateRequest(RequestSchema):
    title: Title
    priority: Priority | None = None


class IssuePriorityRequest(RequestSchema):
    """`null` removes the priority."""

    priority: Priority | None


class IssueSolveRequest(RequestSchema):
    note: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NOTE_MAX)
    ]


class IssueTodoCreateRequest(RequestSchema):
    title: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TODO_TITLE_MAX)
    ]
    owner_id: EntityId
