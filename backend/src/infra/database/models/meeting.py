"""Level 10 meetings: live state, attendance, ratings, frozen summaries."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Sequence,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from src.infra.database.base import Base

TZ = TIMESTAMP(timezone=True)

meeting_id_seq = Sequence("meeting_id_seq", start=1000, metadata=Base.metadata)


class MeetingModel(Base):
    """Postgres is the only source of truth for meeting state (section, timer start)."""

    __tablename__ = "meetings"
    __table_args__ = (
        UniqueConstraint("id", "team_id"),
        CheckConstraint(
            "current_section IN ('scorecard', 'ids', 'conclude')", name="section_valid"
        ),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ended_after_started"),
        # One active meeting per team; a concurrent second start fails here.
        Index(
            "uq_meetings_one_active_per_team",
            "team_id",
            unique=True,
            postgresql_where=text("ended_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, server_default=text("'mt' || nextval('meeting_id_seq')")
    )
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    facilitator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(TZ)
    ended_at: Mapped[datetime | None] = mapped_column(TZ)
    current_section: Mapped[str] = mapped_column(Text, server_default=text("'scorecard'"))
    section_started_at: Mapped[datetime] = mapped_column(TZ)
    state_version: Mapped[int] = mapped_column(Integer, server_default=text("1"))


class MeetingAttendeeModel(Base):
    __tablename__ = "meeting_attendees"

    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(TZ)


class MeetingRatingModel(Base):
    __tablename__ = "meeting_ratings"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 10", name="rating_range"),
        # Only attendees can rate.
        ForeignKeyConstraint(
            ["meeting_id", "user_id"],
            ["meeting_attendees.meeting_id", "meeting_attendees.user_id"],
        ),
    )

    meeting_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    rating: Mapped[int] = mapped_column(SmallInteger)
    updated_at: Mapped[datetime] = mapped_column(TZ)


class MeetingSummaryModel(Base):
    """Snapshot written in the transaction that ends the meeting; never recomputed."""

    __tablename__ = "meeting_summaries"

    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    computed_at: Mapped[datetime] = mapped_column(TZ)
