from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    TEAM_MEMBER = "team_member"
    OBSERVER = "observer"


@dataclass(frozen=True, slots=True)
class User:
    id: str
    company_id: str
    name: str
    email: str
    role: Role

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN

    @property
    def is_read_only(self) -> bool:
        return self.role is Role.OBSERVER

    @property
    def can_own_items(self) -> bool:
        """Observers cannot own Measurables, Rocks, Issues or To-Dos."""
        return not self.is_read_only

    @property
    def ref(self) -> "UserRef":
        return UserRef(id=self.id, name=self.name)


@dataclass(frozen=True, slots=True)
class UserRef:
    """Lightweight reference used in read models (owner, facilitator, attendee)."""

    id: str
    name: str


UNKNOWN_USER_NAME = "Unknown user"


def ref_for(users: dict[str, User], user_id: str) -> UserRef:
    user = users.get(user_id)
    return user.ref if user else UserRef(id=user_id, name=UNKNOWN_USER_NAME)
