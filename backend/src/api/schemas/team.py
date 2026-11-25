from src.api.schemas.common import ResponseSchema
from src.domain.modules.team.entity import TeamAccess


class TeamResponse(ResponseSchema):
    id: str
    name: str


class TeamDetailResponse(TeamResponse):
    can_write: bool

    @classmethod
    def from_access(cls, access: TeamAccess) -> "TeamDetailResponse":
        return cls(id=access.team.id, name=access.team.name, can_write=access.can_write)
