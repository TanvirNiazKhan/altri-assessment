"""Issues and To-Dos.

Cross-entity links use composite FKs `(x_id, team_id) -> parent(id, team_id)` so a row
can never point at another team's data, whatever the application code does.
"""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
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
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from src.infra.database.base import Base

TZ = TIMESTAMP(timezone=True)

# New rows get ids shaped like the seed's ("i1000", "t1000"), from sequences above seed ids.
issue_id_seq = Sequence("issue_id_seq", start=1000, metadata=Base.metadata)
todo_id_seq = Sequence("todo_id_seq", start=1000, metadata=Base.metadata)


class IssueModel(Base):
    __tablename__ = "issues"
    __table_args__ = (
        UniqueConstraint("id", "team_id"),
        CheckConstraint("priority IS NULL OR priority BETWEEN 1 AND 5", name="priority_range"),
        CheckConstraint("char_length(btrim(title)) BETWEEN 1 AND 200", name="title_length"),
        CheckConstraint("(solved_at IS NULL) = (resolution_note IS NULL)", name="solved_has_note"),
        CheckConstraint(
            "resolution_note IS NULL OR btrim(resolution_note) <> ''", name="note_not_blank"
        ),
        CheckConstraint(
            "(source_type IS NULL AND source_measurable_id IS NULL"
            "   AND source_week_start IS NULL AND source_rock_id IS NULL)"
            " OR (source_type = 'measurable' AND source_measurable_id IS NOT NULL"
            "   AND source_week_start IS NOT NULL AND source_rock_id IS NULL)"
            " OR (source_type = 'rock' AND source_rock_id IS NOT NULL"
            "   AND source_measurable_id IS NULL AND source_week_start IS NULL)",
            name="source_consistent",
        ),
        ForeignKeyConstraint(
            ["source_measurable_id", "team_id"], ["measurables.id", "measurables.team_id"]
        ),
        ForeignKeyConstraint(["source_rock_id", "team_id"], ["rocks.id", "rocks.team_id"]),
        ForeignKeyConstraint(
            ["solved_in_meeting_id", "team_id"], ["meetings.id", "meetings.team_id"]
        ),
        # "Make it an Issue" dedupe: at most one unsolved Issue per (Measurable, week) / Rock.
        Index(
            "uq_issues_open_per_measurable_week",
            "source_measurable_id",
            "source_week_start",
            unique=True,
            postgresql_where=text("source_type = 'measurable' AND solved_at IS NULL"),
        ),
        Index(
            "uq_issues_open_per_rock",
            "source_rock_id",
            unique=True,
            postgresql_where=text("source_type = 'rock' AND solved_at IS NULL"),
        ),
        # Serves the Issue-order query for a team's open list.
        Index(
            "ix_issues_open_order",
            "team_id",
            text("priority DESC NULLS LAST"),
            "created_at",
            "id",
            postgresql_where=text("solved_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, server_default=text("'i' || nextval('issue_id_seq')")
    )
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(Text)
    priority: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(TZ)
    solved_at: Mapped[datetime | None] = mapped_column(TZ)
    resolution_note: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str | None] = mapped_column(Text)
    source_measurable_id: Mapped[str | None] = mapped_column(Text)
    source_week_start: Mapped[date | None] = mapped_column(Date)
    source_rock_id: Mapped[str | None] = mapped_column(Text)
    solved_in_meeting_id: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))


class TodoModel(Base):
    __tablename__ = "todos"
    __table_args__ = (
        CheckConstraint("char_length(btrim(title)) BETWEEN 1 AND 200", name="title_length"),
        ForeignKeyConstraint(["source_issue_id", "team_id"], ["issues.id", "issues.team_id"]),
        ForeignKeyConstraint(
            ["created_in_meeting_id", "team_id"], ["meetings.id", "meetings.team_id"]
        ),
        Index("ix_todos_team_id_due_date", "team_id", "due_date"),
    )

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, server_default=text("'t' || nextval('todo_id_seq')")
    )
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(Text)
    due_date: Mapped[date] = mapped_column(Date)
    done_at: Mapped[datetime | None] = mapped_column(TZ)
    source_issue_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TZ)
    created_in_meeting_id: Mapped[str | None] = mapped_column(Text)
