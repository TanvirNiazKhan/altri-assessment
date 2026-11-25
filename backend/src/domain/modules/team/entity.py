from dataclasses import dataclass

from src.domain.modules.user.entity import User


@dataclass(frozen=True, slots=True)
class Team:
    id: str
    company_id: str
    name: str


@dataclass(frozen=True, slots=True)
class TeamAccess:
    """Result of an authorization check: who is acting on which team, and how."""

    user: User
    team: Team
    can_write: bool


def can_read_team(user: User, team: Team, *, is_member: bool) -> bool:
    return user.company_id == team.company_id and (user.is_admin or is_member)


def can_write_team(user: User, team: Team, *, is_member: bool) -> bool:
    return can_read_team(user, team, is_member=is_member) and not user.is_read_only
