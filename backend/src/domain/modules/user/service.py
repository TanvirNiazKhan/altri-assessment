from collections.abc import Sequence

from src.domain.modules.user.entity import User
from src.domain.modules.user.exceptions import NotAuthenticatedError, UserNotFoundError
from src.domain.modules.user.repository import UserRepository


class UserService:
    """Seeded-user switcher: no passwords (out of scope)."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def get(self, user_id: str) -> User:
        user = await self._users.get(user_id)
        if user is None:
            raise UserNotFoundError()
        return user

    async def list_users(self) -> Sequence[User]:
        return await self._users.list_all()

    async def resolve_session_user(self, user_id: str | None) -> User:
        """User behind a session; a missing/deleted user is unauthenticated, not 404."""
        user = await self._users.get(user_id) if user_id else None
        if user is None:
            raise NotAuthenticatedError()
        return user
