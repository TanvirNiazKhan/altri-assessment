from src.domain.shared.exceptions import (
    BusinessRuleViolationError,
    NotFoundError,
    PermissionDeniedError,
)


class TeamNotFoundError(NotFoundError):
    """Raised for missing *and* inaccessible teams, so ids cannot be probed."""

    code, message = "team_not_found", "Team not found"


class TeamReadOnlyError(PermissionDeniedError):
    code, message = "forbidden_role", "Your role cannot change this team's data"


class InvalidOwnerError(BusinessRuleViolationError):
    code, message = "invalid_owner", "Owner must be an Admin or Team Member of this team"
