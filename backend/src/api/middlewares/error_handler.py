"""Maps every error to RFC 9457 `application/problem+json`.

- DomainError            -> status from STATUS_BY_ERROR (raised by services / repositories)
- RequestValidationError -> 422 with field errors
- HTTPException          -> its status (e.g. unknown route 404)
- anything else          -> 500, generic body; full traceback logged with the request id
"""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.middlewares.request_id import HEADER as REQUEST_ID_HEADER
from src.domain.shared.exceptions import (
    AuthenticationError,
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    StaleVersionError,
)

PROBLEM_JSON = "application/problem+json"
log = logging.getLogger(__name__)

# Most specific base class wins (looked up along the exception's MRO).
STATUS_BY_ERROR: dict[type[DomainError], int] = {
    AuthenticationError: 401,
    PermissionDeniedError: 403,
    NotFoundError: 404,
    ConflictError: 409,
    StaleVersionError: 412,
    BusinessRuleViolationError: 422,
}


def status_for(exc: DomainError) -> int:
    for cls in type(exc).__mro__:
        if cls in STATUS_BY_ERROR:
            return STATUS_BY_ERROR[cls]
    return 500


def problem(
    request: Request, status: int, code: str, detail: str | None = None, **extra: Any
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "code": code,
    }
    if detail:
        body["detail"] = detail
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        body["request_id"] = request_id
    body.update(extra)
    response = JSONResponse(jsonable_encoder(body), status_code=status, media_type=PROBLEM_JSON)
    if request_id:
        # A 500 bypasses RequestIdMiddleware's send hook, so set the header here too.
        response.headers[REQUEST_ID_HEADER] = request_id
    return response


async def _domain_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    return problem(request, status_for(exc), exc.code, exc.message, **exc.details)


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [
        {"loc": list(e.get("loc", ())), "msg": e.get("msg"), "type": e.get("type")}
        for e in exc.errors()
    ]
    return problem(request, 422, "validation_error", "Request validation failed", errors=errors)


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = HTTPStatus(exc.status_code).phrase.lower().replace(" ", "_")
    detail = exc.detail if isinstance(exc.detail, str) else None
    return problem(request, exc.status_code, code, detail)


async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    """Last resort. Never leaks internals; the request id links the client to the log."""
    log.exception(
        "unhandled error request_id=%s %s %s",
        getattr(request.state, "request_id", None),
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return problem(request, 500, "internal_error", "An unexpected error occurred")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    # Registered on Exception, Starlette runs this in ServerErrorMiddleware (outermost).
    app.add_exception_handler(Exception, _unhandled_error)
