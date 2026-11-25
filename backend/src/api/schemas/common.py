from decimal import Decimal
from typing import Annotated, Any

from fastapi import Path
from pydantic import BaseModel, ConfigDict, PlainSerializer, StringConstraints


class ResponseSchema(BaseModel):
    """Response body: built from domain entities (dataclasses) via attributes."""

    model_config = ConfigDict(from_attributes=True)


class RequestSchema(BaseModel):
    """Request body: unknown fields rejected, strings trimmed."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Problem(BaseModel):
    """RFC 9457 problem details (documents error responses in OpenAPI)."""

    type: str = "about:blank"
    title: str
    status: int
    code: str
    detail: str | None = None
    request_id: str | None = None
    errors: list[dict[str, Any]] | None = None


PROBLEM_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": Problem, "description": "Not authenticated"},
    403: {"model": Problem, "description": "Role not allowed"},
    404: {"model": Problem, "description": "Not found or not accessible"},
    409: {"model": Problem, "description": "Conflicts with current state"},
    422: {"model": Problem, "description": "Validation error"},
}


ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
EntityId = Annotated[str, StringConstraints(pattern=ID_PATTERN)]
IdPath = Annotated[str, Path(pattern=ID_PATTERN)]

# Decimals travel as JSON numbers (not strings) in responses.
Number = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class UserRefResponse(ResponseSchema):
    id: str
    name: str
