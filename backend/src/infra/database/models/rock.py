"""Quarterly Rocks and their Milestones."""

from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.base import Base


class RockModel(Base):
    __tablename__ = "rocks"
    __table_args__ = (
        UniqueConstraint("id", "team_id"),
        CheckConstraint(r"quarter ~ '^\d{4}-Q[1-4]$'", name="quarter_format"),
        CheckConstraint(
            "seeded_status IN ('on_track', 'off_track', 'complete')", name="seeded_status_valid"
        ),
        Index("ix_rocks_team_id_quarter", "team_id", "quarter"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(Text)
    quarter: Mapped[str] = mapped_column(Text)
    seeded_status: Mapped[str] = mapped_column(Text)

    milestones: Mapped[list["MilestoneModel"]] = relationship(
        back_populates="rock", order_by="MilestoneModel.due_date, MilestoneModel.id", lazy="raise"
    )


class MilestoneModel(Base):
    __tablename__ = "milestones"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    rock_id: Mapped[str] = mapped_column(ForeignKey("rocks.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    due_date: Mapped[date] = mapped_column(Date)
    done: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))

    rock: Mapped[RockModel] = relationship(back_populates="milestones", lazy="raise")
