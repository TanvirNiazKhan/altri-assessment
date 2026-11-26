"""ORM model -> domain entity conversion. Entities never leak SQLAlchemy objects."""

from src.domain.modules.company.entity import Company
from src.domain.modules.issue.entity import Issue, IssueSource, IssueSourceType
from src.domain.modules.meeting.entity import Meeting, MeetingSection, Rating
from src.domain.modules.rock.entity import Milestone, Rock, RockStatus
from src.domain.modules.scorecard.entity import Goal, GoalType, Measurable, Score
from src.domain.modules.team.entity import Team
from src.domain.modules.todo.entity import Todo
from src.domain.modules.user.entity import Role, User
from src.infra.database.models import (
    CompanyModel,
    IssueModel,
    MeasurableModel,
    MeetingModel,
    MeetingRatingModel,
    MilestoneModel,
    RockModel,
    ScoreModel,
    TeamModel,
    TodoModel,
    UserModel,
)


def to_user(m: UserModel) -> User:
    return User(id=m.id, company_id=m.company_id, name=m.name, email=m.email, role=Role(m.role))


def to_team(m: TeamModel) -> Team:
    return Team(id=m.id, company_id=m.company_id, name=m.name)


def to_company(m: CompanyModel) -> Company:
    return Company(id=m.id, name=m.name, timezone=m.timezone)


def to_measurable(m: MeasurableModel) -> Measurable:
    return Measurable(
        id=m.id,
        team_id=m.team_id,
        owner_id=m.owner_id,
        name=m.name,
        unit=m.unit,
        goal=Goal(GoalType(m.goal_type), value=m.goal_value, min=m.goal_min, max=m.goal_max),
    )


def to_score(m: ScoreModel) -> Score:
    return Score(
        measurable_id=m.measurable_id,
        week_start=m.week_start,
        value=m.value,
        updated_at=m.updated_at,
        updated_by=m.updated_by,
        version=m.version,
    )


def to_issue(m: IssueModel) -> Issue:
    source = (
        IssueSource(
            type=IssueSourceType(m.source_type),
            measurable_id=m.source_measurable_id,
            week_start=m.source_week_start,
            rock_id=m.source_rock_id,
        )
        if m.source_type
        else None
    )
    return Issue(
        id=m.id,
        team_id=m.team_id,
        owner_id=m.owner_id,
        title=m.title,
        created_at=m.created_at,
        priority=m.priority,
        solved_at=m.solved_at,
        resolution_note=m.resolution_note,
        source=source,
        solved_in_meeting_id=m.solved_in_meeting_id,
        version=m.version,
    )


def to_todo(m: TodoModel) -> Todo:
    return Todo(
        id=m.id,
        team_id=m.team_id,
        owner_id=m.owner_id,
        title=m.title,
        due_date=m.due_date,
        created_at=m.created_at,
        done_at=m.done_at,
        source_issue_id=m.source_issue_id,
        created_in_meeting_id=m.created_in_meeting_id,
    )


def to_milestone(m: MilestoneModel) -> Milestone:
    return Milestone(id=m.id, rock_id=m.rock_id, title=m.title, due_date=m.due_date, done=m.done)


def to_rock(m: RockModel) -> Rock:
    return Rock(
        id=m.id,
        team_id=m.team_id,
        owner_id=m.owner_id,
        title=m.title,
        quarter=m.quarter,
        seeded_status=RockStatus(m.seeded_status),
        milestones=tuple(to_milestone(ms) for ms in m.milestones),
    )


def to_meeting(m: MeetingModel) -> Meeting:
    return Meeting(
        id=m.id,
        team_id=m.team_id,
        facilitator_id=m.facilitator_id,
        started_at=m.started_at,
        current_section=MeetingSection(m.current_section),
        section_started_at=m.section_started_at,
        ended_at=m.ended_at,
        state_version=m.state_version,
    )


def to_rating(m: MeetingRatingModel) -> Rating:
    return Rating(user_id=m.user_id, rating=m.rating, updated_at=m.updated_at)
