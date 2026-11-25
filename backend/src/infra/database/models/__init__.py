"""SQLAlchemy ORM models (persistence shape). Domain entities live in src.domain.modules.

Every model is imported here so `Base.metadata` is complete for Alembic and tests.
"""

from src.infra.database.base import Base
from src.infra.database.models.meeting import (
    MeetingAttendeeModel,
    MeetingModel,
    MeetingRatingModel,
    MeetingSummaryModel,
    meeting_id_seq,
)
from src.infra.database.models.organization import (
    CompanyModel,
    MembershipModel,
    TeamModel,
    UserModel,
)
from src.infra.database.models.rock import MilestoneModel, RockModel
from src.infra.database.models.scorecard import MeasurableModel, ScoreModel
from src.infra.database.models.work import IssueModel, TodoModel, issue_id_seq, todo_id_seq

ID_SEQUENCES = (issue_id_seq, todo_id_seq, meeting_id_seq)

__all__ = [
    "ID_SEQUENCES",
    "Base",
    "CompanyModel",
    "IssueModel",
    "MeasurableModel",
    "MeetingAttendeeModel",
    "MeetingModel",
    "MeetingRatingModel",
    "MeetingSummaryModel",
    "MembershipModel",
    "MilestoneModel",
    "RockModel",
    "ScoreModel",
    "TeamModel",
    "TodoModel",
    "UserModel",
]
