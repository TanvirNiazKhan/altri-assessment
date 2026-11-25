from collections.abc import Sequence

from sqlalchemy import select

from src.domain.modules.company.entity import Company
from src.domain.modules.company.repository import CompanyRepository
from src.infra.database.models import CompanyModel
from src.infra.database.repositories.base import SqlRepository
from src.infra.database.repositories.mappers import to_company


class SqlCompanyRepository(SqlRepository, CompanyRepository):
    async def get(self, company_id: str) -> Company | None:
        m = await self._s.get(CompanyModel, company_id)
        return to_company(m) if m else None

    async def list_all(self) -> Sequence[Company]:
        rows = await self._s.scalars(select(CompanyModel).order_by(CompanyModel.id))
        return [to_company(m) for m in rows]
