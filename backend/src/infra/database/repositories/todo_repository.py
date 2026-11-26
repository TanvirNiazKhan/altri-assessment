from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import select, update

from src.domain.modules.todo.entity import Todo
from src.domain.modules.todo.repository import TodoRepository
from src.infra.database.errors import translate_db_errors
from src.infra.database.models import IssueModel, TodoModel
from src.infra.database.repositories.base import SqlRepository
from src.infra.database.repositories.mappers import to_todo


class SqlTodoRepository(SqlRepository, TodoRepository):
    async def list(self, team_id: str) -> Sequence[Todo]:
        stmt = (
            select(TodoModel)
            .where(TodoModel.team_id == team_id)
            .order_by(TodoModel.due_date, TodoModel.id)
        )
        return [to_todo(m) for m in await self._s.scalars(stmt)]

    async def list_created_in_meeting(self, meeting_id: str) -> Sequence[Todo]:
        stmt = select(TodoModel).where(TodoModel.created_in_meeting_id == meeting_id)
        return [to_todo(m) for m in await self._s.scalars(stmt)]

    async def get(self, team_id: str, todo_id: str) -> Todo | None:
        stmt = (
            select(TodoModel)
            .where(TodoModel.id == todo_id, TodoModel.team_id == team_id)
            .execution_options(populate_existing=True)
        )
        m = await self._s.scalar(stmt)
        return to_todo(m) if m else None

    async def add(
        self,
        *,
        team_id: str,
        owner_id: str,
        title: str,
        due_date: date,
        created_at: datetime,
        source_issue_id: str | None,
        created_in_meeting_id: str | None,
    ) -> Todo:
        model = TodoModel(
            team_id=team_id,
            owner_id=owner_id,
            title=title,
            due_date=due_date,
            created_at=created_at,
            source_issue_id=source_issue_id,
            created_in_meeting_id=created_in_meeting_id,
        )
        self._s.add(model)
        await self._flush()
        await self._s.refresh(model)
        return to_todo(model)

    async def set_done_at(self, team_id: str, todo_id: str, done_at: datetime | None) -> Todo:
        async with translate_db_errors():
            await self._s.execute(
                update(TodoModel)
                .where(TodoModel.id == todo_id, TodoModel.team_id == team_id)
                .values(done_at=done_at)
            )
        todo = await self.get(team_id, todo_id)
        assert todo is not None
        return todo

    async def issue_titles(self, issue_ids: Sequence[str]) -> dict[str, str]:
        if not issue_ids:
            return {}
        rows = await self._s.execute(
            select(IssueModel.id, IssueModel.title).where(IssueModel.id.in_(set(issue_ids)))
        )
        return {iid: title for iid, title in rows}
