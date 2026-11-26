from datetime import date

from src.api.schemas.common import ResponseSchema, UserRefResponse
from src.domain.modules.rock.entity import RockStatus, RockView


class MilestoneResponse(ResponseSchema):
    id: str
    title: str
    due_date: date
    done: bool


class RockResponse(ResponseSchema):
    id: str
    title: str
    quarter: str
    owner: UserRefResponse
    status: RockStatus
    progress_percent: int
    milestones: list[MilestoneResponse]

    @classmethod
    def from_domain(cls, v: RockView) -> "RockResponse":
        r = v.rock
        return cls(
            id=r.id,
            title=r.title,
            quarter=r.quarter,
            owner=UserRefResponse(id=r.owner_id, name=v.owner_name),
            status=v.status,
            progress_percent=v.progress_percent,
            milestones=[
                MilestoneResponse(id=m.id, title=m.title, due_date=m.due_date, done=m.done)
                for m in r.milestones
            ],
        )
