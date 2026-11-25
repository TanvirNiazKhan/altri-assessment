"""Companies, teams, users and memberships."""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infra.database.base import Base


class CompanyModel(Base):
    __tablename__ = "companies"
    __table_args__ = (CheckConstraint("btrim(timezone) <> ''", name="timezone_not_blank"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(Text)


class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(Text)


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'team_member', 'observer')", name="role_valid"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, unique=True)
    role: Mapped[str] = mapped_column(Text)


class MembershipModel(Base):
    __tablename__ = "memberships"
    __table_args__ = (Index("ix_memberships_team_id", "team_id"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), primary_key=True)
