"""Roles (brief 2.4) and team boundaries, enforced on the server.

Seed: u1 Admin (team_lead only), u2 Team Member (team_lead + team_sales),
u5 Observer (team_lead), u6 Team Member (team_sales only), team_ops has neither u2 nor u5.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import LoginAs

pytestmark = pytest.mark.db

TEAM_READS = [
    "/api/teams/{t}",
    "/api/teams/{t}/members",
    "/api/teams/{t}/scorecard",
    "/api/teams/{t}/issues",
    "/api/teams/{t}/issues?status=solved",
    "/api/teams/{t}/todos",
    "/api/teams/{t}/rocks",
    "/api/teams/{t}/meetings",
    "/api/teams/{t}/meetings/active",
]

# (method, path, body) for every write action on the Team and Meeting pages.
TEAM_WRITES = [
    ("PUT", "/api/teams/team_lead/scorecard/measurables/m1/weeks/2026-11-09", {"value": 3}),
    ("POST", "/api/teams/team_lead/scorecard/measurables/m1/weeks/2026-10-26/issue", None),
    ("POST", "/api/teams/team_lead/issues", {"title": "x"}),
    ("PATCH", "/api/teams/team_lead/issues/i1", {"priority": 1}),
    ("POST", "/api/teams/team_lead/issues/i1/solve", {"note": "done"}),
    ("POST", "/api/teams/team_lead/issues/i1/todos", {"title": "x", "owner_id": "u2"}),
    ("PUT", "/api/teams/team_lead/todos/t12/done", None),
    ("DELETE", "/api/teams/team_lead/todos/t1/done", None),
    ("POST", "/api/teams/team_lead/meetings", None),
]


@pytest.mark.parametrize("path", TEAM_READS)
async def test_team_member_cannot_read_another_team(login_as: LoginAs, path: str) -> None:
    u2 = await login_as("u2")  # not a member of team_ops
    r = await u2.get(path.format(t="team_ops"))
    assert (r.status_code, r.json()["code"]) == (404, "team_not_found")


async def test_inaccessible_and_nonexistent_team_are_indistinguishable(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    a, b = await u2.get("/api/teams/team_ops/issues"), await u2.get("/api/teams/nope/issues")
    assert a.status_code == b.status_code == 404
    assert a.json()["code"] == b.json()["code"] == "team_not_found"


async def test_child_ids_are_team_scoped(login_as: LoginAs) -> None:
    """u2 can read team_lead and team_sales; i8 belongs to team_sales."""
    u2 = await login_as("u2")
    assert (await u2.get("/api/teams/team_sales/issues/i8")).status_code == 200
    r = await u2.get("/api/teams/team_lead/issues/i8")
    assert (r.status_code, r.json()["code"]) == (404, "issue_not_found")
    r = await u2.post("/api/teams/team_lead/issues/i8/solve", json={"note": "sneaky"})
    assert r.status_code == 404
    r = await u2.put(
        "/api/teams/team_lead/scorecard/measurables/m6/weeks/2026-11-09", json={"value": 1}
    )
    assert (r.status_code, r.json()["code"]) == (404, "measurable_not_found")


@pytest.mark.parametrize(("method", "path", "body"), TEAM_WRITES)
async def test_observer_writes_are_refused(
    login_as: LoginAs, method: str, path: str, body: dict[str, object] | None
) -> None:
    u5 = await login_as("u5")
    r = await u5.request(method, path, json=body)
    assert (r.status_code, r.json()["code"]) == (403, "forbidden_role")


async def test_observer_reads_everything_in_own_team(login_as: LoginAs) -> None:
    u5 = await login_as("u5")
    for path in TEAM_READS:
        assert (await u5.get(path.format(t="team_lead"))).status_code == 200, path
    assert (await u5.get("/api/teams/team_lead")).json()["can_write"] is False


@pytest.mark.parametrize(("method", "path", "body"), TEAM_WRITES)
async def test_team_member_writes_in_own_team(
    login_as: LoginAs, method: str, path: str, body: dict[str, object] | None
) -> None:
    u3 = await login_as("u3")
    r = await u3.request(method, path, json=body)
    assert r.status_code in (200, 201), r.text


async def test_admin_can_act_in_any_team(login_as: LoginAs) -> None:
    u1 = await login_as("u1")  # Admin, member of team_lead only
    teams = {t["id"] for t in (await u1.get("/api/me")).json()["teams"]}
    assert teams == {"team_lead", "team_sales", "team_ops"}
    r = await u1.post("/api/teams/team_ops/issues", json={"title": "Admin issue"})
    assert r.status_code == 201


async def test_unauthenticated_requests_are_refused(client: AsyncClient) -> None:
    for path in TEAM_READS:
        r = await client.get(path.format(t="team_lead"))
        assert (r.status_code, r.json()["code"]) == (401, "not_authenticated"), path


async def test_forged_session_cookie_is_refused(client: AsyncClient) -> None:
    client.cookies.set("l10_session", "u1")
    assert (await client.get("/api/me")).status_code == 401
