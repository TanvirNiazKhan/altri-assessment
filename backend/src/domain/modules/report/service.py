"""Rules report (brief 2.6): every computed value for every team, as of `now`.

"As of now" so the report is meaningful at any APP_NOW: facts with a timestamp only count
once they have happened (To-Dos created/done, Issues created/solved, meetings ended).
Facts without one (scores, Milestone done flags, seeded Rock status) are used as stored.
"""

from datetime import datetime
from typing import Any

from src.domain.modules.company.entity import Company
from src.domain.modules.issue.entity import order_issues
from src.domain.modules.issue.repository import IssueRepository
from src.domain.modules.meeting.repository import MeetingRepository
from src.domain.modules.meeting.service import MeetingService
from src.domain.modules.rock.repository import RockRepository
from src.domain.modules.scorecard.entity import SCORECARD_WEEKS
from src.domain.modules.scorecard.repository import ScorecardRepository
from src.domain.modules.team.repository import TeamRepository
from src.domain.modules.todo.entity import Completion, weekly_completion
from src.domain.modules.todo.repository import TodoRepository
from src.domain.shared.calendar import CalendarContext, week_bounds_utc, week_window

Json = dict[str, Any]


def _iso_utc(instant: datetime) -> str:
    return instant.isoformat().replace("+00:00", "Z")


def _completion_json(c: Completion | None) -> Json | None:
    if c is None:
        return None
    return {
        "due": c.due,
        "done": c.done,
        "rate_percent": c.rate_percent,
        "meets_target": c.meets_target,
    }


class RulesReportService:
    def __init__(
        self,
        teams: TeamRepository,
        scorecard: ScorecardRepository,
        todos: TodoRepository,
        rocks: RockRepository,
        issues: IssueRepository,
        meetings: MeetingRepository,
        meeting_service: MeetingService,
    ) -> None:
        self._teams = teams
        self._scorecard = scorecard
        self._todos = todos
        self._rocks = rocks
        self._issues = issues
        self._meetings = meetings
        self._meeting_service = meeting_service

    async def build(self, company: Company, now: datetime) -> Json:
        cal = CalendarContext.at(now, company.zone)
        teams = sorted(await self._teams.list_by_company(company.id), key=lambda t: t.id)
        return {
            "now": _iso_utc(now),
            "teams": {t.id: await self._team(t.id, cal) for t in teams},
        }

    async def _team(self, team_id: str, cal: CalendarContext) -> Json:
        weeks = week_window(cal.current_week, SCORECARD_WEEKS)
        now = cal.now

        measurables = await self._scorecard.list_measurables(team_id)
        scores = await self._scorecard.list_scores([m.id for m in measurables], weeks[0], weeks[-1])
        values = {(s.measurable_id, s.week_start): s.value for s in scores}
        measurable_status = {
            m.id: {
                w.isoformat(): m.status_for(
                    values.get((m.id, w)), week_start=w, current_week=cal.current_week
                ).value
                for w in weeks
            }
            for m in sorted(measurables, key=lambda m: m.id)
        }

        todos = [t for t in await self._todos.list(team_id) if t.created_at <= now]
        todo_completion = {
            w.isoformat(): _completion_json(
                weekly_completion(
                    todos, week_start=w, week_end_utc=week_bounds_utc(w, cal.tz)[1], now=now
                )
            )
            for w in weeks
        }
        overdue = sorted(t.id for t in todos if t.is_overdue(today=cal.today, now=now))

        rocks = {
            r.id: {"status": r.status(cal.today).value, "progress_percent": r.progress_percent()}
            for r in sorted(
                await self._rocks.list_for_quarter(team_id, cal.quarter), key=lambda r: r.id
            )
        }

        open_issues = [i for i in await self._issues.list_all(team_id) if i.is_open_as_of(now)]
        issue_order = [i.id for i in order_issues(open_issues)]

        meetings: Json = {}
        ended = [
            m
            for m in await self._meetings.list_ended(team_id)
            if m.ended_at is not None and m.ended_at <= now
        ]
        for meeting in sorted(ended, key=lambda m: m.id):
            summary = await self._meeting_service.build_summary(meeting, cal.tz)
            meetings[meeting.id] = {
                "scorecard_week": summary.scorecard_week.isoformat(),
                "measurable_status": {
                    sm.id: sm.status.value for sm in sorted(summary.measurables, key=lambda x: x.id)
                },
                "issues_solved": sorted(i.id for i in summary.issues_solved),
                "todos_created": sorted(t.id for t in summary.todos_created),
                "attendee_ids": sorted(a.id for a in summary.attendees),
                "rating": float(summary.average_rating)
                if summary.average_rating is not None
                else None,
            }

        return {
            "measurable_status": measurable_status,
            "todo_completion": todo_completion,
            "overdue_todos": overdue,
            "rocks": rocks,
            "issue_order": issue_order,
            "meetings": meetings,
        }
