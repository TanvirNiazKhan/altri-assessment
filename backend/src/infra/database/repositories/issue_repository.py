from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert

from src.domain.modules.issue.entity import Issue, IssueSourceType
from src.domain.modules.issue.repository import IssueRepository
from src.infra.database.errors import translate_db_errors
from src.infra.database.models import IssueModel
from src.infra.database.repositories.base import SqlRepository
from src.infra.database.repositories.mappers import to_issue

# Must match the predicate of uq_issues_open_per_measurable_week exactly, so Postgres can
# infer the partial unique index as the ON CONFLICT arbiter.
_OPEN_MEASURABLE_ISSUE = text("source_type = 'measurable' AND solved_at IS NULL")

ISSUE_ORDER = (
    IssueModel.priority.desc().nulls_last(),
    IssueModel.created_at,
    IssueModel.id,
)


class SqlIssueRepository(SqlRepository, IssueRepository):
    async def list_open(self, team_id: str) -> Sequence[Issue]:
        stmt = (
            select(IssueModel)
            .where(IssueModel.team_id == team_id, IssueModel.solved_at.is_(None))
            .order_by(*ISSUE_ORDER)
        )
        return [to_issue(m) for m in await self._s.scalars(stmt)]

    async def list_solved(self, team_id: str) -> Sequence[Issue]:
        stmt = (
            select(IssueModel)
            .where(IssueModel.team_id == team_id, IssueModel.solved_at.is_not(None))
            .order_by(IssueModel.solved_at.desc(), IssueModel.id)
        )
        return [to_issue(m) for m in await self._s.scalars(stmt)]

    async def list_all(self, team_id: str) -> Sequence[Issue]:
        stmt = select(IssueModel).where(IssueModel.team_id == team_id).order_by(IssueModel.id)
        return [to_issue(m) for m in await self._s.scalars(stmt)]

    async def list_solved_in_meeting(self, meeting_id: str) -> Sequence[Issue]:
        stmt = select(IssueModel).where(IssueModel.solved_in_meeting_id == meeting_id)
        return [to_issue(m) for m in await self._s.scalars(stmt)]

    async def get(self, team_id: str, issue_id: str) -> Issue | None:
        stmt = (
            select(IssueModel)
            .where(IssueModel.id == issue_id, IssueModel.team_id == team_id)
            .execution_options(populate_existing=True)
        )
        m = await self._s.scalar(stmt)
        return to_issue(m) if m else None

    async def add(
        self, team_id: str, owner_id: str, title: str, priority: int | None, created_at: datetime
    ) -> Issue:
        model = IssueModel(
            team_id=team_id,
            owner_id=owner_id,
            title=title,
            priority=priority,
            created_at=created_at,
        )
        self._s.add(model)
        await self._flush()
        await self._s.refresh(model)
        return to_issue(model)

    async def add_from_measurable_or_get(
        self,
        team_id: str,
        owner_id: str,
        title: str,
        created_at: datetime,
        measurable_id: str,
        week_start: date,
    ) -> tuple[Issue, bool]:
        # One statement, race-free: a concurrent insert of the same (measurable, week)
        # blocks on the partial unique index until the other transaction commits, then
        # DO NOTHING. The follow-up SELECT runs with a fresh snapshot and sees that row.
        stmt = (
            insert(IssueModel)
            .values(
                team_id=team_id,
                owner_id=owner_id,
                title=title,
                created_at=created_at,
                source_type=IssueSourceType.MEASURABLE.value,
                source_measurable_id=measurable_id,
                source_week_start=week_start,
            )
            .on_conflict_do_nothing(
                index_elements=[IssueModel.source_measurable_id, IssueModel.source_week_start],
                index_where=_OPEN_MEASURABLE_ISSUE,
            )
            .returning(IssueModel.id)
        )
        async with translate_db_errors():
            new_id = await self._s.scalar(stmt)
        if new_id is not None:
            created = await self.get(team_id, new_id)
            assert created is not None
            return created, True

        existing = await self._s.scalar(
            select(IssueModel)
            .where(
                IssueModel.team_id == team_id,
                IssueModel.source_type == IssueSourceType.MEASURABLE.value,
                IssueModel.source_measurable_id == measurable_id,
                IssueModel.source_week_start == week_start,
                IssueModel.solved_at.is_(None),
            )
            .execution_options(populate_existing=True)
        )
        if existing is None:  # solved between our insert and select: try once more
            return await self.add_from_measurable_or_get(
                team_id, owner_id, title, created_at, measurable_id, week_start
            )
        return to_issue(existing), False

    async def set_priority(self, team_id: str, issue_id: str, priority: int | None) -> Issue:
        async with translate_db_errors():
            await self._s.execute(
                update(IssueModel)
                .where(IssueModel.id == issue_id, IssueModel.team_id == team_id)
                .values(priority=priority, version=IssueModel.version + 1)
            )
        issue = await self.get(team_id, issue_id)
        assert issue is not None
        return issue

    async def solve(
        self,
        team_id: str,
        issue_id: str,
        note: str,
        solved_at: datetime,
        meeting_id: str | None,
    ) -> Issue | None:
        async with translate_db_errors():
            solved_id = await self._s.scalar(
                update(IssueModel)
                .where(
                    IssueModel.id == issue_id,
                    IssueModel.team_id == team_id,
                    IssueModel.solved_at.is_(None),
                )
                .values(
                    solved_at=solved_at,
                    resolution_note=note,
                    solved_in_meeting_id=meeting_id,
                    version=IssueModel.version + 1,
                )
                .returning(IssueModel.id)
            )
        return await self.get(team_id, issue_id) if solved_id else None

    async def open_measurable_issue_ids(self, team_id: str) -> dict[tuple[str, date], str]:
        rows = await self._s.execute(
            select(
                IssueModel.source_measurable_id, IssueModel.source_week_start, IssueModel.id
            ).where(
                IssueModel.team_id == team_id,
                IssueModel.source_type == IssueSourceType.MEASURABLE.value,
                IssueModel.solved_at.is_(None),
            )
        )
        return {(mid, week): iid for mid, week, iid in rows if mid and week}
