from src.domain.shared.exceptions import NotFoundError


class TodoNotFoundError(NotFoundError):
    code, message = "todo_not_found", "To-Do not found"
