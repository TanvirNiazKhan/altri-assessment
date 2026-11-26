"""Load seed.json. Rerunnable: one transaction, skipped entirely if already seeded.

Meeting provenance (which Issues were solved / To-Dos created in which meeting) is not
in the file, so it is derived here once from each meeting's [started_at, ended_at] window.
"""

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.modules.company.entity import Company
from src.domain.modules.issue.entity import IssueSourceType
from src.domain.modules.meeting.entity import MeetingSection
from src.domain.modules.meeting.service import MeetingService
from src.infra.database.models import (
    ID_SEQUENCES,
    Base,
    CompanyModel,
    IssueModel,
    MeasurableModel,
    MeetingAttendeeModel,
    MeetingModel,
    MeetingRatingModel,
    MembershipModel,
    MilestoneModel,
    RockModel,
    ScoreModel,
    TeamModel,
    TodoModel,
    UserModel,
)

log = logging.getLogger(__name__)
Seed = dict[str, Any]


def read_seed(path: Path) -> Seed:
    data: Seed = json.loads(path.read_text())
    return data


def _dt(v: str | None) -> datetime | None:
    return datetime.fromisoformat(v) if v else None


def _req_dt(v: str) -> datetime:
    return datetime.fromisoformat(v)


def _d(v: str) -> date:
    return date.fromisoformat(v)


def _num(v: float | int | None) -> Decimal | None:
    return None if v is None else Decimal(str(v))


def _meeting_for(
    team_id: str, at: datetime | None, windows: list[tuple[str, str, datetime, datetime]]
) -> str | None:
    if at is None:
        return None
    for mid, tid, start, end in windows:
        if tid == team_id and start <= at <= end:
            return mid
    return None


async def is_seeded(session: AsyncSession, seed: Seed) -> bool:
    return await session.get(CompanyModel, seed["company"]["id"]) is not None


async def load_seed(session: AsyncSession, seed: Seed) -> bool:
    """Insert the seed. Returns False (no-op) if it is already present. Caller commits."""
    if await is_seeded(session, seed):
        return False

    c = seed["company"]
    session.add(CompanyModel(id=c["id"], name=c["name"], timezone=c["timezone"]))
    await session.flush()

    session.add_all(
        TeamModel(id=t["id"], company_id=c["id"], name=t["name"]) for t in seed["teams"]
    )
    session.add_all(
        UserModel(id=u["id"], company_id=c["id"], name=u["name"], email=u["email"], role=u["role"])
        for u in seed["users"]
    )
    await session.flush()
    session.add_all(MembershipModel(**m) for m in seed["memberships"])

    session.add_all(
        MeasurableModel(
            id=m["id"],
            team_id=m["team_id"],
            owner_id=m["owner_id"],
            name=m["name"],
            unit=m["unit"],
            goal_type=m["goal"]["type"],
            goal_value=_num(m["goal"].get("value")),
            goal_min=_num(m["goal"].get("min")),
            goal_max=_num(m["goal"].get("max")),
            sort_order=i,
        )
        for i, m in enumerate(seed["measurables"])
    )
    session.add_all(
        RockModel(
            id=r["id"],
            team_id=r["team_id"],
            owner_id=r["owner_id"],
            title=r["title"],
            quarter=r["quarter"],
            seeded_status=r["status"],
        )
        for r in seed["rocks"]
    )
    await session.flush()

    session.add_all(
        ScoreModel(
            measurable_id=s["measurable_id"], week_start=_d(s["week_start"]), value=_num(s["value"])
        )
        for s in seed["scores"]
        if s["value"] is not None
    )
    session.add_all(
        MilestoneModel(
            id=ms["id"],
            rock_id=ms["rock_id"],
            title=ms["title"],
            due_date=_d(ms["due_date"]),
            done=ms["done"],
        )
        for ms in seed["milestones"]
    )

    # Meetings: insert active, add attendees + ratings, then end it (the ratings trigger
    # rejects writes on ended meetings, and only one meeting per team may be active).
    windows: list[tuple[str, str, datetime, datetime]] = []
    for mt in seed["meetings"]:
        started, ended = _req_dt(mt["started_at"]), _req_dt(mt["ended_at"])
        meeting = MeetingModel(
            id=mt["id"],
            team_id=mt["team_id"],
            facilitator_id=mt["facilitator_id"],
            started_at=started,
            current_section=MeetingSection.CONCLUDE,
            section_started_at=started,
        )
        session.add(meeting)
        await session.flush()
        session.add_all(
            MeetingAttendeeModel(meeting_id=mt["id"], user_id=uid, joined_at=started)
            for uid in mt["attendee_ids"]
        )
        await session.flush()
        session.add_all(
            MeetingRatingModel(
                meeting_id=mt["id"], user_id=r["user_id"], rating=r["rating"], updated_at=ended
            )
            for r in mt["ratings"]
        )
        await session.flush()
        meeting.ended_at = ended
        await session.flush()
        windows.append((mt["id"], mt["team_id"], started, ended))

    for i in seed["issues"]:
        src = i.get("source")
        session.add(
            IssueModel(
                id=i["id"],
                team_id=i["team_id"],
                owner_id=i["owner_id"],
                title=i["title"],
                priority=i["priority"],
                created_at=_req_dt(i["created_at"]),
                solved_at=_dt(i["solved_at"]),
                resolution_note=i["resolution_note"],
                source_type=IssueSourceType.MEASURABLE if src else None,
                source_measurable_id=src["measurable_id"] if src else None,
                source_week_start=_d(src["week_start"]) if src else None,
                solved_in_meeting_id=_meeting_for(i["team_id"], _dt(i["solved_at"]), windows),
            )
        )
    await session.flush()

    session.add_all(
        TodoModel(
            id=t["id"],
            team_id=t["team_id"],
            owner_id=t["owner_id"],
            title=t["title"],
            due_date=_d(t["due_date"]),
            done_at=_dt(t["done_at"]),
            source_issue_id=t["source_issue_id"],
            created_at=_req_dt(t["created_at"]),
            created_in_meeting_id=_meeting_for(t["team_id"], _dt(t["created_at"]), windows),
        )
        for t in seed["todos"]
    )
    await session.flush()
    await _snapshot_meeting_summaries(session, seed)
    log.info("seed loaded: %d issues, %d todos", len(seed["issues"]), len(seed["todos"]))
    return True


async def truncate_all(session: AsyncSession) -> None:
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    await session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    for seq in ID_SEQUENCES:
        await session.execute(text(f"ALTER SEQUENCE {seq.name} RESTART WITH {seq.start}"))


async def _snapshot_meeting_summaries(session: AsyncSession, seed: Seed) -> None:
    """Freeze the seeded meetings' summaries with the same code that ends a live meeting."""
    # Local imports: repositories import the models this module also uses.
    from src.infra.database.repositories import (
        SqlIssueRepository,
        SqlMeetingRepository,
        SqlScorecardRepository,
        SqlTodoRepository,
        SqlUserRepository,
    )
    from src.infra.database.unit_of_work import SqlUnitOfWork
    from src.infra.realtime.publisher import NullEventPublisher

    company = Company(**seed["company"])
    meetings_repo = SqlMeetingRepository(session)
    service = MeetingService(
        meetings_repo,
        SqlScorecardRepository(session),
        SqlIssueRepository(session),
        SqlTodoRepository(session),
        SqlUserRepository(session),
        SqlUnitOfWork(session),
        NullEventPublisher(),
    )
    for mt in seed["meetings"]:
        meeting = await meetings_repo.get(mt["team_id"], mt["id"])
        assert meeting is not None and meeting.ended_at is not None
        summary = await service.build_summary(meeting, company.zone)
        await meetings_repo.save_summary(summary, computed_at=meeting.ended_at)
