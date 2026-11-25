"""Company repository interface (port). Implemented in src.infra.database.repositories."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.domain.modules.company.entity import Company


class CompanyRepository(ABC):
    @abstractmethod
    async def get(self, company_id: str) -> Company | None: ...

    @abstractmethod
    async def list_all(self) -> Sequence[Company]: ...
