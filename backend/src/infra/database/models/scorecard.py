"""Measurables and their weekly scores."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from src.infra.database.base import Base

TZ = TIMESTAMP(timezone=True)


class MeasurableModel(Base):
    __tablename__ = "measurables"
    __table_args__ = (
        UniqueConstraint("id", "team_id"),  # target of composite (team-scoped) FKs
        CheckConstraint(
            "goal_type IN ('at_least', 'at_most', 'between', 'exactly')", name="goal_type_valid"
        ),
        CheckConstraint(
            "(goal_type = 'between' AND goal_min IS NOT NULL AND goal_max IS NOT NULL"
            " AND goal_min <= goal_max AND goal_value IS NULL)"
            " OR (goal_type <> 'between' AND goal_value IS NOT NULL"
            " AND goal_min IS NULL AND goal_max IS NULL)",
            name="goal_shape",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(Text)
    goal_type: Mapped[str] = mapped_column(Text)
    goal_value: Mapped[Decimal | None] = mapped_column(Numeric)
    goal_min: Mapped[Decimal | None] = mapped_column(Numeric)
    goal_max: Mapped[Decimal | None] = mapped_column(Numeric)
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))


class ScoreModel(Base):
    __tablename__ = "scores"
    __table_args__ = (
        CheckConstraint("EXTRACT(ISODOW FROM week_start) = 1", name="week_start_is_monday"),
    )

    measurable_id: Mapped[str] = mapped_column(ForeignKey("measurables.id"), primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric)
    updated_at: Mapped[datetime | None] = mapped_column(TZ)
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
