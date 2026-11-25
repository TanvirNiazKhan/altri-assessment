from pydantic import Field

from src.api.schemas.common import RequestSchema, ResponseSchema
from src.domain.modules.user.entity import Role


class UserResponse(ResponseSchema):
    id: str
    name: str
    email: str
    role: Role


class LoginRequest(RequestSchema):
    user_id: str = Field(min_length=1, max_length=64)
