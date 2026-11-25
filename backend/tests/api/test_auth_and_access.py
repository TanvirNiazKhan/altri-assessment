"""API tests. Non-`db` tests need no database; `db` tests read the seeded Postgres."""

import pytest
from httpx import AsyncClient


async def login(client: AsyncClient, user_id: str) -> None:
    r = await client.post("/api/auth/login", json={"user_id": user_id})
    assert r.status_code == 200, r.text


async def test_liveness(client: AsyncClient) -> None:
    r = await client.get("/api/health")
    assert r.json() == {"status": "ok"}


async def test_request_id_is_generated_or_propagated(client: AsyncClient) -> None:
    assert len((await client.get("/api/health")).headers["x-request-id"]) == 32
    r = await client.get("/api/health", headers={"X-Request-ID": "abc-123"})
    assert r.headers["x-request-id"] == "abc-123"


async def test_validation_error_is_problem_json(client: AsyncClient) -> None:
    r = await client.post("/api/auth/login", json={"user_id": "u1", "extra": 1})
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["code"] == "validation_error" and body["request_id"]


@pytest.mark.db
async def test_unauthenticated_is_401(client: AsyncClient) -> None:
    r = await client.get("/api/me")
    assert (r.status_code, r.json()["code"]) == (401, "not_authenticated")


@pytest.mark.db
async def test_me_returns_calendar_from_app_now(client: AsyncClient) -> None:
    await login(client, "u2")
    body = (await client.get("/api/me")).json()
    assert body["calendar"]["current_week"] == "2026-11-09"
    assert body["calendar"]["quarter"] == "2026-Q4"
    assert {t["id"] for t in body["teams"]} == {"team_lead", "team_sales"}


@pytest.mark.db
async def test_admin_sees_every_team(client: AsyncClient) -> None:
    await login(client, "u1")
    teams = {t["id"] for t in (await client.get("/api/me")).json()["teams"]}
    assert {"team_lead", "team_sales", "team_ops"} <= teams


@pytest.mark.db
async def test_non_member_and_unknown_team_both_404(client: AsyncClient) -> None:
    await login(client, "u2")  # member of team_lead + team_sales, not team_ops
    a = await client.get("/api/teams/team_ops")
    b = await client.get("/api/teams/does_not_exist")
    assert a.status_code == b.status_code == 404
    a_body, b_body = a.json(), b.json()
    a_body.pop("request_id"), b_body.pop("request_id")
    assert a_body == b_body


@pytest.mark.db
async def test_observer_is_read_only(client: AsyncClient) -> None:
    await login(client, "u5")
    r = await client.get("/api/teams/team_lead")
    assert r.status_code == 200
    assert r.json()["can_write"] is False


@pytest.mark.db
async def test_members_can_own_excludes_observers(client: AsyncClient) -> None:
    await login(client, "u2")
    ids = {u["id"] for u in (await client.get("/api/teams/team_lead/members?can_own=true")).json()}
    assert "u5" not in ids and "u2" in ids


@pytest.mark.db
async def test_unknown_user_login_404(client: AsyncClient) -> None:
    r = await client.post("/api/auth/login", json={"user_id": "nope"})
    assert (r.status_code, r.json()["code"]) == (404, "user_not_found")
