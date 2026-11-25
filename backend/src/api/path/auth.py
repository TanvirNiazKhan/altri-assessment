from fastapi import APIRouter, Response, status

from src.api.schemas.common import PROBLEM_RESPONSES
from src.api.schemas.user import LoginRequest, UserResponse
from src.config.dependency import SessionSignerDep, SettingsDep, UserServiceDep

router = APIRouter(prefix="/auth", tags=["auth"], responses=PROBLEM_RESPONSES)


@router.get("/users", summary="Users for the login picker")
async def list_users(users: UserServiceDep) -> list[UserResponse]:
    return [UserResponse.model_validate(u) for u in await users.list_users()]


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    users: UserServiceDep,
    signer: SessionSignerDep,
    settings: SettingsDep,
) -> UserResponse:
    user = await users.get(body.user_id)
    response.set_cookie(
        settings.session_cookie_name,
        signer.sign(user.id),
        max_age=settings.session_max_age_s,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, settings: SettingsDep) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")
