import pytest

from src.domain.modules.user.exceptions import NotAuthenticatedError, UserNotFoundError
from src.domain.modules.user.service import UserService
from tests.domain.fakes import ADMIN, MEMBER, FakeUserRepository


@pytest.fixture
def service() -> UserService:
    return UserService(FakeUserRepository([ADMIN, MEMBER]))


async def test_get_unknown_user_is_not_found(service: UserService) -> None:
    with pytest.raises(UserNotFoundError):
        await service.get("nope")


@pytest.mark.parametrize("user_id", [None, "", "deleted"])
async def test_session_without_valid_user_is_unauthenticated(
    service: UserService, user_id: str | None
) -> None:
    with pytest.raises(NotAuthenticatedError):
        await service.resolve_session_user(user_id)


async def test_session_user_resolves(service: UserService) -> None:
    assert await service.resolve_session_user("u2") == MEMBER
