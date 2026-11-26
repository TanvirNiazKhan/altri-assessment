"""Every SQL repository implements its domain interface completely."""

import inspect
from abc import ABC

import pytest

from src.domain.modules.company.repository import CompanyRepository
from src.domain.modules.issue.repository import IssueRepository
from src.domain.modules.meeting.repository import MeetingRepository
from src.domain.modules.rock.repository import RockRepository
from src.domain.modules.scorecard.repository import ScorecardRepository
from src.domain.modules.team.repository import TeamRepository
from src.domain.modules.todo.repository import TodoRepository
from src.domain.modules.user.repository import UserRepository
from src.domain.shared.events import EventPublisher
from src.domain.shared.unit_of_work import UnitOfWork
from src.infra.database.repositories import (
    SqlCompanyRepository,
    SqlIssueRepository,
    SqlMeetingRepository,
    SqlRockRepository,
    SqlScorecardRepository,
    SqlTeamRepository,
    SqlTodoRepository,
    SqlUserRepository,
)
from src.infra.database.unit_of_work import SqlUnitOfWork
from src.infra.realtime.publisher import NullEventPublisher, PgEventPublisher


@pytest.mark.parametrize(
    ("implementation", "interface"),
    [
        (SqlUserRepository, UserRepository),
        (SqlTeamRepository, TeamRepository),
        (SqlCompanyRepository, CompanyRepository),
        (SqlScorecardRepository, ScorecardRepository),
        (SqlIssueRepository, IssueRepository),
        (SqlTodoRepository, TodoRepository),
        (SqlRockRepository, RockRepository),
        (SqlMeetingRepository, MeetingRepository),
        (SqlUnitOfWork, UnitOfWork),
        (PgEventPublisher, EventPublisher),
        (NullEventPublisher, EventPublisher),
    ],
)
def test_implements_domain_interface(implementation: type, interface: type[ABC]) -> None:
    assert issubclass(implementation, interface)
    assert not inspect.isabstract(implementation), "missing abstract method implementations"
