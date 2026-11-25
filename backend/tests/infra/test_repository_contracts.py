"""Every SQL repository implements its domain interface completely."""

import inspect
from abc import ABC

import pytest

from src.domain.modules.company.repository import CompanyRepository
from src.domain.modules.team.repository import TeamRepository
from src.domain.modules.user.repository import UserRepository
from src.domain.shared.unit_of_work import UnitOfWork
from src.infra.database.repositories import (
    SqlCompanyRepository,
    SqlTeamRepository,
    SqlUserRepository,
)
from src.infra.database.unit_of_work import SqlUnitOfWork


@pytest.mark.parametrize(
    ("implementation", "interface"),
    [
        (SqlUserRepository, UserRepository),
        (SqlTeamRepository, TeamRepository),
        (SqlCompanyRepository, CompanyRepository),
        (SqlUnitOfWork, UnitOfWork),
    ],
)
def test_implements_domain_interface(implementation: type, interface: type[ABC]) -> None:
    assert issubclass(implementation, interface)
    assert not inspect.isabstract(implementation), "missing abstract method implementations"
