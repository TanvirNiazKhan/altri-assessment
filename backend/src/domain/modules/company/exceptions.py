from src.domain.shared.exceptions import NotFoundError


class CompanyNotFoundError(NotFoundError):
    code, message = "company_not_found", "Company not found"
