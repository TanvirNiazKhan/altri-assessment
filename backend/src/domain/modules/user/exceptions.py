from src.domain.shared.exceptions import AuthenticationError, NotFoundError


class UserNotFoundError(NotFoundError):
    code, message = "user_not_found", "Unknown user"


class NotAuthenticatedError(AuthenticationError):
    code, message = "not_authenticated", "Log in first"
