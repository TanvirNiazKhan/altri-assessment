from src.domain.modules.company.entity import Company
from src.domain.modules.company.exceptions import CompanyNotFoundError
from src.domain.modules.company.repository import CompanyRepository
from src.domain.modules.user.entity import User
from src.domain.shared.calendar import CalendarContext
from src.domain.shared.clock import Clock


class CompanyService:
    def __init__(self, companies: CompanyRepository, clock: Clock) -> None:
        self._companies = companies
        self._clock = clock

    async def get(self, company_id: str) -> Company:
        company = await self._companies.get(company_id)
        if company is None:
            raise CompanyNotFoundError()
        return company

    async def calendar_for(self, user: User) -> CalendarContext:
        """Today / current week / quarter in the user's company time zone."""
        company = await self.get(user.company_id)
        return CalendarContext.at(self._clock.now(), company.zone)
