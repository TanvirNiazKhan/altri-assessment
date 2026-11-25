"""Translate database integrity errors into domain errors.

Postgres enforces invariants (CHECKs, team-scoped FKs, partial unique indexes, triggers).
When one fires, SQLAlchemy raises `IntegrityError`. Repositories and the unit of work run
writes inside `translate_db_errors()`, so services and the API only ever see `DomainError`s:
a known constraint maps to a specific, stable error code; anything else falls back to a
generic error chosen by SQLSTATE. Constraint names are logged, never sent to clients.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from src.domain.shared.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
)

log = logging.getLogger(__name__)

# SQLSTATE class 23: integrity constraint violation.
UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"
CHECK_VIOLATION = "23514"
NOT_NULL_VIOLATION = "23502"
EXCLUSION_VIOLATION = "23P01"


@dataclass(frozen=True, slots=True)
class KnownConstraint:
    error: type[DomainError]
    code: str
    message: str


# Constraints that encode a business rule get their own stable code.
KNOWN_CONSTRAINTS: dict[str, KnownConstraint] = {
    "observer_cannot_own": KnownConstraint(
        BusinessRuleViolationError,
        "observer_cannot_own",
        "Observers cannot own or facilitate items",
    ),
    "rating_meeting_ended": KnownConstraint(
        ConflictError, "meeting_ended", "The meeting has ended; ratings are frozen"
    ),
    "uq_meetings_one_active_per_team": KnownConstraint(
        ConflictError, "meeting_already_active", "This team already has an active meeting"
    ),
    "uq_issues_open_per_measurable_week": KnownConstraint(
        ConflictError, "issue_already_open", "An open Issue already exists for this week"
    ),
    "uq_issues_open_per_rock": KnownConstraint(
        ConflictError, "issue_already_open", "An open Issue already exists for this Rock"
    ),
}

# Fallback by SQLSTATE when the constraint is not listed above.
GENERIC_BY_SQLSTATE: dict[str, KnownConstraint] = {
    UNIQUE_VIOLATION: KnownConstraint(ConflictError, "duplicate", "Resource already exists"),
    EXCLUSION_VIOLATION: KnownConstraint(ConflictError, "conflict", "Conflicts with existing data"),
    FOREIGN_KEY_VIOLATION: KnownConstraint(
        BusinessRuleViolationError, "invalid_reference", "Referenced resource does not exist"
    ),
    CHECK_VIOLATION: KnownConstraint(
        BusinessRuleViolationError, "constraint_violation", "Value violates a data rule"
    ),
    NOT_NULL_VIOLATION: KnownConstraint(
        BusinessRuleViolationError, "missing_value", "A required value is missing"
    ),
}


def _sqlstate(exc: IntegrityError) -> str | None:
    orig = exc.orig
    state = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    return state if isinstance(state, str) else None


def _constraint_name(exc: IntegrityError) -> str | None:
    # asyncpg's exception (with `constraint_name`) is the cause of the DBAPI adapter error.
    for candidate in (exc.orig, getattr(exc.orig, "__cause__", None)):
        name = getattr(candidate, "constraint_name", None)
        if isinstance(name, str):
            return name
    return None


def to_domain_error(exc: IntegrityError) -> DomainError | None:
    """Domain error for `exc`, or None if it is not an integrity violation we understand."""
    sqlstate, constraint = _sqlstate(exc), _constraint_name(exc)
    known = KNOWN_CONSTRAINTS.get(constraint or "") or GENERIC_BY_SQLSTATE.get(sqlstate or "")
    if known is None:
        return None
    log.info(
        "integrity violation sqlstate=%s constraint=%s -> %s", sqlstate, constraint, known.code
    )
    return known.error(known.message, code=known.code)


@asynccontextmanager
async def translate_db_errors() -> AsyncIterator[None]:
    try:
        yield
    except IntegrityError as exc:
        domain_error = to_domain_error(exc)
        if domain_error is None:
            raise
        raise domain_error from exc
