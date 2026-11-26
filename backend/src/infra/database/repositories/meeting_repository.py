from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from src.domain.modules.meeting.entity import Meeting, MeetingSection, Rating
from src.domain.modules.meeting.repository import MeetingRepository
from src.domain.modules.meeting.summary import (
    MeetingSummary,
    SummaryIssue,
    SummaryMeasurable,
    SummaryRating,
    SummaryTodo,
)
from src.domain.modules.scorecard.entity import MeasurableStatus
from src.domain.modules.user.entity import UserRef
from src.infra.database.errors import translate_db_errors
from src.infra.database.models import (
    MeetingAttendeeModel,
    MeetingModel,
    MeetingRatingModel,
    MeetingSummaryModel,
)
from src.infra.database.repositories.base import SqlRepository
from src.infra.database.repositories.mappers import to_meeting, to_rating


class SqlMeetingRepository(SqlRepository, MeetingRepository):
    async def get_active(self, team_id: str) -> Meeting | None:
        stmt = (
            select(MeetingModel)
            .where(MeetingModel.team_id == team_id, MeetingModel.ended_at.is_(None))
            .execution_options(populate_existing=True)
        )
        m = await self._s.scalar(stmt)
        return to_meeting(m) if m else None

    async def get(self, team_id: str, meeting_id: str) -> Meeting | None:
        stmt = (
            select(MeetingModel)
            .where(MeetingModel.id == meeting_id, MeetingModel.team_id == team_id)
            .execution_options(populate_existing=True)
        )
        m = await self._s.scalar(stmt)
        return to_meeting(m) if m else None

    async def list_ended(self, team_id: str) -> Sequence[Meeting]:
        stmt = (
            select(MeetingModel)
            .where(MeetingModel.team_id == team_id, MeetingModel.ended_at.is_not(None))
            .order_by(MeetingModel.ended_at.desc(), MeetingModel.id)
        )
        return [to_meeting(m) for m in await self._s.scalars(stmt)]

    async def create(self, team_id: str, facilitator_id: str, now: datetime) -> Meeting:
        model = MeetingModel(
            team_id=team_id,
            facilitator_id=facilitator_id,
            started_at=now,
            current_section=MeetingSection.SCORECARD.value,
            section_started_at=now,
        )
        self._s.add(model)
        await self._flush()
        await self._s.refresh(model)
        return to_meeting(model)

    async def add_attendee(self, meeting_id: str, user_id: str, joined_at: datetime) -> bool:
        stmt = (
            insert(MeetingAttendeeModel)
            .values(meeting_id=meeting_id, user_id=user_id, joined_at=joined_at)
            .on_conflict_do_nothing(index_elements=["meeting_id", "user_id"])
            .returning(MeetingAttendeeModel.user_id)
        )
        async with translate_db_errors():
            return await self._s.scalar(stmt) is not None

    async def list_attendees(self, meeting_id: str) -> Sequence[tuple[str, datetime]]:
        rows = await self._s.execute(
            select(MeetingAttendeeModel.user_id, MeetingAttendeeModel.joined_at)
            .where(MeetingAttendeeModel.meeting_id == meeting_id)
            .order_by(MeetingAttendeeModel.joined_at, MeetingAttendeeModel.user_id)
        )
        return [(uid, joined) for uid, joined in rows]

    async def advance(
        self,
        team_id: str,
        meeting_id: str,
        *,
        facilitator_id: str,
        expected: MeetingSection,
        to: MeetingSection,
        now: datetime,
    ) -> Meeting | None:
        updated = await self._s.scalar(
            update(MeetingModel)
            .where(
                MeetingModel.id == meeting_id,
                MeetingModel.team_id == team_id,
                MeetingModel.facilitator_id == facilitator_id,
                MeetingModel.ended_at.is_(None),
                MeetingModel.current_section == expected.value,
            )
            .values(
                current_section=to.value,
                section_started_at=now,
                state_version=MeetingModel.state_version + 1,
            )
            .returning(MeetingModel.id)
        )
        return await self.get(team_id, meeting_id) if updated else None

    async def end(
        self, team_id: str, meeting_id: str, *, facilitator_id: str, now: datetime
    ) -> Meeting | None:
        async with translate_db_errors():
            updated = await self._s.scalar(
                update(MeetingModel)
                .where(
                    MeetingModel.id == meeting_id,
                    MeetingModel.team_id == team_id,
                    MeetingModel.facilitator_id == facilitator_id,
                    MeetingModel.ended_at.is_(None),
                )
                .values(ended_at=now, state_version=MeetingModel.state_version + 1)
                .returning(MeetingModel.id)
            )
        return await self.get(team_id, meeting_id) if updated else None

    async def upsert_rating(
        self, meeting_id: str, user_id: str, rating: int, now: datetime
    ) -> None:
        stmt = insert(MeetingRatingModel).values(
            meeting_id=meeting_id, user_id=user_id, rating=rating, updated_at=now
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["meeting_id", "user_id"],
            set_={"rating": stmt.excluded.rating, "updated_at": stmt.excluded.updated_at},
        )
        async with translate_db_errors():
            await self._s.execute(stmt)

    async def list_ratings(self, meeting_id: str) -> Sequence[Rating]:
        stmt = (
            select(MeetingRatingModel)
            .where(MeetingRatingModel.meeting_id == meeting_id)
            .order_by(MeetingRatingModel.user_id)
            .execution_options(populate_existing=True)
        )
        return [to_rating(m) for m in await self._s.scalars(stmt)]

    async def save_summary(self, summary: MeetingSummary, computed_at: datetime) -> None:
        stmt = insert(MeetingSummaryModel).values(
            meeting_id=summary.meeting_id, payload=summary_to_json(summary), computed_at=computed_at
        )
        # Written once: a snapshot is never overwritten.
        await self._s.execute(stmt.on_conflict_do_nothing(index_elements=["meeting_id"]))

    async def get_summary(self, meeting_id: str) -> MeetingSummary | None:
        m = await self._s.get(MeetingSummaryModel, meeting_id)
        return summary_from_json(m.payload) if m else None


# --------------------------------------------------------------------- snapshot (JSONB)


def _ref(r: UserRef) -> dict[str, str]:
    return {"id": r.id, "name": r.name}


def summary_to_json(s: MeetingSummary) -> dict[str, Any]:
    return {
        "meeting_id": s.meeting_id,
        "team_id": s.team_id,
        "facilitator": _ref(s.facilitator),
        "started_at": s.started_at.isoformat(),
        "ended_at": s.ended_at.isoformat(),
        "scorecard_week": s.scorecard_week.isoformat(),
        "measurables": [
            {
                "id": m.id,
                "name": m.name,
                "unit": m.unit,
                "value": str(m.value) if m.value is not None else None,
                "status": m.status.value,
            }
            for m in s.measurables
        ],
        "issues_solved": [
            {"id": i.id, "title": i.title, "resolution_note": i.resolution_note}
            for i in s.issues_solved
        ],
        "todos_created": [
            {
                "id": t.id,
                "title": t.title,
                "owner": _ref(t.owner),
                "due_date": t.due_date.isoformat(),
            }
            for t in s.todos_created
        ],
        "attendees": [_ref(a) for a in s.attendees],
        "ratings": [{"user": _ref(r.user), "rating": r.rating} for r in s.ratings],
        "average_rating": str(s.average_rating) if s.average_rating is not None else None,
    }


def summary_from_json(d: dict[str, Any]) -> MeetingSummary:
    def ref(x: dict[str, str]) -> UserRef:
        return UserRef(id=x["id"], name=x["name"])

    return MeetingSummary(
        meeting_id=d["meeting_id"],
        team_id=d["team_id"],
        facilitator=ref(d["facilitator"]),
        started_at=datetime.fromisoformat(d["started_at"]),
        ended_at=datetime.fromisoformat(d["ended_at"]),
        scorecard_week=date.fromisoformat(d["scorecard_week"]),
        measurables=tuple(
            SummaryMeasurable(
                id=m["id"],
                name=m["name"],
                unit=m["unit"],
                value=Decimal(m["value"]) if m["value"] is not None else None,
                status=MeasurableStatus(m["status"]),
            )
            for m in d["measurables"]
        ),
        issues_solved=tuple(
            SummaryIssue(id=i["id"], title=i["title"], resolution_note=i["resolution_note"])
            for i in d["issues_solved"]
        ),
        todos_created=tuple(
            SummaryTodo(
                id=t["id"],
                title=t["title"],
                owner=ref(t["owner"]),
                due_date=date.fromisoformat(t["due_date"]),
            )
            for t in d["todos_created"]
        ),
        attendees=tuple(ref(a) for a in d["attendees"]),
        ratings=tuple(SummaryRating(user=ref(r["user"]), rating=r["rating"]) for r in d["ratings"]),
        average_rating=Decimal(d["average_rating"]) if d["average_rating"] is not None else None,
    )
