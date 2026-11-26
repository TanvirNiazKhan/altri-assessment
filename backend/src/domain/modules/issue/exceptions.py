from src.domain.shared.exceptions import ConflictError, NotFoundError


class IssueNotFoundError(NotFoundError):
    code, message = "issue_not_found", "Issue not found"


class IssueAlreadySolvedError(ConflictError):
    code, message = "issue_already_solved", "Issue is already solved"
