"""IntegrityError -> DomainError translation."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import build_engine, build_sessionmaker
from src.config.settings import Settings
from src.domain.shared.exceptions import BusinessRuleViolationError, ConflictError
from src.infra.database.errors import (
    CHECK_VIOLATION,
    FOREIGN_KEY_VIOLATION,
    UNIQUE_VIOLATION,
    to_domain_error,
    translate_db_errors,
)
from src.infra.database.models import IssueModel, MeetingModel
from src.infra.database.repositories.base import SqlRepository
from src.infra.database.unit_of_work import SqlUnitOfWork

# ------------------------------------------------------------------ pure translation


class _AsyncpgError(Exception):
    def __init__(self, constraint: str | None) -> None:
        self.constraint_name = constraint


class _DbapiError(Exception):
    """Shape of SQLAlchemy's asyncpg adapter error: sqlstate + asyncpg cause."""

    def __init__(self, sqlstate: str, constraint: str | None) -> None:
        self.sqlstate = sqlstate
        self.__cause__ = _AsyncpgError(constraint)


def integrity(sqlstate: str, constraint: str | None = None) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, _DbapiError(sqlstate, constraint))


@pytest.mark.parametrize(
    ("sqlstate", "constraint", "error", "code"),
    [
        (CHECK_VIOLATION, "observer_cannot_own", BusinessRuleViolationError, "observer_cannot_own"),
        (
            UNIQUE_VIOLATION,
            "uq_meetings_one_active_per_team",
            ConflictError,
            "meeting_already_active",
        ),
        (
            UNIQUE_VIOLATION,
            "uq_issues_open_per_measurable_week",
            ConflictError,
            "issue_already_open",
        ),
        (UNIQUE_VIOLATION, "uq_users_email", ConflictError, "duplicate"),
        (FOREIGN_KEY_VIOLATION, "fk_x", BusinessRuleViolationError, "invalid_reference"),
        (
            CHECK_VIOLATION,
            "ck_issues_priority_range",
            BusinessRuleViolationError,
            "constraint_violation",
        ),
    ],
)
def test_known_and_generic_mappings(
    sqlstate: str, constraint: str, error: type[Exception], code: str
) -> None:
    domain_error = to_domain_error(integrity(sqlstate, constraint))
    assert isinstance(domain_error, error)
    assert domain_error.code == code


def test_constraint_name_never_reaches_the_client_message() -> None:
    domain_error = to_domain_error(integrity(CHECK_VIOLATION, "ck_issues_priority_range"))
    assert domain_error is not None
    assert "ck_issues" not in domain_error.message and not domain_error.details


async def test_context_manager_chains_original_error() -> None:
    original = integrity(UNIQUE_VIOLATION, "uq_users_email")
    with pytest.raises(ConflictError) as caught:
        async with translate_db_errors():
            raise original
    assert caught.value.__cause__ is original


async def test_unknown_sqlstate_is_reraised_untouched() -> None:
    original = integrity("99999")
    with pytest.raises(IntegrityError) as caught:
        async with translate_db_errors():
            raise original
    assert caught.value is original


# ------------------------------------------------------------------ real Postgres (rolled back)

NOW = datetime(2026, 11, 11, 15, tzinfo=UTC)


@pytest.fixture
async def session(settings: Settings) -> AsyncIterator[AsyncSession]:
    engine = build_engine(settings)
    async with build_sessionmaker(engine)() as s:
        yield s
        await s.rollback()
    await engine.dispose()


class _WriteRepository(SqlRepository):
    async def add(self, *rows: object) -> None:
        self._s.add_all(rows)
        await self._flush()


@pytest.mark.db
async def test_trigger_violation_on_flush_becomes_domain_error(session: AsyncSession) -> None:
    observer_owned = IssueModel(team_id="team_lead", owner_id="u5", title="x", created_at=NOW)
    with pytest.raises(BusinessRuleViolationError) as caught:
        await _WriteRepository(session).add(observer_owned)
    assert caught.value.code == "observer_cannot_own"


@pytest.mark.db
async def test_partial_unique_index_on_commit_becomes_conflict(session: AsyncSession) -> None:
    def meeting() -> MeetingModel:
        return MeetingModel(
            team_id="team_sales", facilitator_id="u2", started_at=NOW, section_started_at=NOW
        )

    session.add_all([meeting(), meeting()])
    with pytest.raises(ConflictError) as caught:
        await SqlUnitOfWork(session).commit()
    assert caught.value.code == "meeting_already_active"
