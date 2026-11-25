"""Base domain errors. Framework-free: the API layer maps them to HTTP status codes."""

from typing import Any


class DomainError(Exception):
    code: str = "domain_error"
    message: str = "Domain error"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(DomainError):
    code, message = "not_authenticated", "Authentication required"


class PermissionDeniedError(DomainError):
    code, message = "permission_denied", "Not allowed"


class NotFoundError(DomainError):
    code, message = "not_found", "Resource not found"


class ConflictError(DomainError):
    code, message = "conflict", "Conflicts with the current state"


class StaleVersionError(DomainError):
    code, message = "stale_version", "Resource changed since it was read"


class BusinessRuleViolationError(DomainError):
    code, message = "business_rule_violation", "Business rule violated"
