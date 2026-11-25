"""ORM model -> domain entity conversion. Entities never leak SQLAlchemy objects."""

from src.domain.modules.company.entity import Company
from src.domain.modules.team.entity import Team
from src.domain.modules.user.entity import Role, User
from src.infra.database.models import CompanyModel, TeamModel, UserModel


def to_user(m: UserModel) -> User:
    return User(id=m.id, company_id=m.company_id, name=m.name, email=m.email, role=Role(m.role))


def to_team(m: TeamModel) -> Team:
    return Team(id=m.id, company_id=m.company_id, name=m.name)


def to_company(m: CompanyModel) -> Company:
    return Company(id=m.id, name=m.name, timezone=m.timezone)
