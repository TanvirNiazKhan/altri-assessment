"""Every failure leaves the API as problem+json, including unexpected ones."""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.domain.shared.exceptions import ConflictError


@pytest.fixture
async def raw_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Client that receives the server's 500 response instead of re-raising the error."""

    async def boom() -> None:
        raise RuntimeError("secret internal detail")

    async def conflict() -> None:
        raise ConflictError(code="issue_already_open")

    app.add_api_route("/api/_test/boom", boom)
    app.add_api_route("/api/_test/conflict", conflict)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_unexpected_error_is_generic_500_problem(
    raw_client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    r = await raw_client.get("/api/_test/boom", headers={"X-Request-ID": "req-42"})

    assert r.status_code == 500
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.headers["x-request-id"] == "req-42"
    body = r.json()
    assert body["code"] == "internal_error" and body["request_id"] == "req-42"
    assert "secret" not in r.text  # no internals leak
    logged = [rec for rec in caplog.records if "unhandled error" in rec.getMessage()]
    assert logged and "req-42" in logged[0].getMessage() and logged[0].exc_info


async def test_domain_error_status_comes_from_base_class(raw_client: AsyncClient) -> None:
    r = await raw_client.get("/api/_test/conflict")
    assert (r.status_code, r.json()["code"]) == (409, "issue_already_open")


async def test_unknown_route_is_problem_json(raw_client: AsyncClient) -> None:
    r = await raw_client.get("/api/nope")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")
