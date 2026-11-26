import asyncio

import pytest
from httpx import AsyncClient

from src.infra.services.clock import FrozenClock
from tests.conftest import LoginAs

pytestmark = pytest.mark.db

BASE = "/api/teams/team_lead/meetings"


async def start(c: AsyncClient) -> dict:  # type: ignore[type-arg]
    r = await c.post(BASE)
    assert r.status_code == 201, r.text
    return r.json()["meeting"]  # type: ignore[no-any-return]


async def advance(c: AsyncClient, mid: str, expected: str) -> dict:  # type: ignore[type-arg]
    r = await c.post(f"{BASE}/{mid}/advance", json={"expected_section": expected})
    assert r.status_code == 200, r.text
    return r.json()["meeting"]  # type: ignore[no-any-return]


async def test_start_makes_caller_facilitator_and_attendee(login_as: LoginAs) -> None:
    u3 = await login_as("u3")
    m = await start(u3)
    assert m["facilitator"]["id"] == "u3"
    assert m["current_section"] == "scorecard" and m["section_duration_s"] == 300
    assert [a["id"] for a in m["attendees"]] == ["u3"]
    assert [a["section"] for a in m["agenda"]] == ["scorecard", "ids", "conclude"]
    active = (await u3.get(f"{BASE}/active")).json()
    assert active["meeting"]["id"] == m["id"]
    assert active["server_now"] == "2026-11-11T15:00:00Z"


async def test_one_active_meeting_per_team(login_as: LoginAs) -> None:
    u2, u3 = await login_as("u2"), await login_as("u3")
    m = await start(u3)
    r = await u2.post(BASE)
    assert (r.status_code, r.json()["code"], r.json()["meeting_id"]) == (
        409,
        "meeting_already_active",
        m["id"],
    )


async def test_concurrent_starts_yield_one_meeting(login_as: LoginAs) -> None:
    clients = [await login_as(u) for u in ("u1", "u2", "u3", "u4")]
    responses = await asyncio.gather(*(c.post(BASE) for c in clients * 3))
    assert sorted(r.status_code for r in responses) == [201] + [409] * 11


async def test_anyone_who_can_read_can_join_observer_included(login_as: LoginAs) -> None:
    u3, u5 = await login_as("u3"), await login_as("u5")
    m = await start(u3)
    r = await u5.post(f"{BASE}/{m['id']}/join")
    assert r.status_code == 200
    attendees = {a["id"]: a for a in r.json()["meeting"]["attendees"]}
    assert attendees["u5"]["role"] == "observer" and attendees["u5"]["can_rate"] is False
    again = await u5.post(f"{BASE}/{m['id']}/join")  # idempotent (refresh / reconnect)
    assert len(again.json()["meeting"]["attendees"]) == 2


async def test_only_facilitator_advances_and_ends(login_as: LoginAs) -> None:
    u2, u3 = await login_as("u2"), await login_as("u3")
    m = await start(u3)
    await u2.post(f"{BASE}/{m['id']}/join")
    r = await u2.post(f"{BASE}/{m['id']}/advance", json={"expected_section": "scorecard"})
    assert (r.status_code, r.json()["code"]) == (403, "not_facilitator")
    r = await u2.post(f"{BASE}/{m['id']}/end")
    assert (r.status_code, r.json()["code"]) == (403, "not_facilitator")


async def test_advance_is_guarded_against_stale_clients(login_as: LoginAs) -> None:
    u3 = await login_as("u3")
    m = await start(u3)
    after = await advance(u3, m["id"], "scorecard")
    assert after["current_section"] == "ids" and after["state_version"] == m["state_version"] + 1
    stale = await u3.post(f"{BASE}/{m['id']}/advance", json={"expected_section": "scorecard"})
    assert (stale.status_code, stale.json()["code"]) == (409, "section_conflict")
    await advance(u3, m["id"], "ids")
    last = await u3.post(f"{BASE}/{m['id']}/advance", json={"expected_section": "conclude"})
    assert (last.status_code, last.json()["code"]) == (409, "no_next_section")


async def test_timer_is_server_owned_and_never_auto_advances(
    login_as: LoginAs, clock: FrozenClock
) -> None:
    u3 = await login_as("u3")
    m = await start(u3)
    clock.advance(7 * 60)  # Scorecard is 5 minutes: 2 minutes over
    state = (await u3.get(f"{BASE}/active")).json()
    assert state["meeting"]["current_section"] == "scorecard"
    assert state["meeting"]["section_started_at"] == m["section_started_at"]
    assert state["server_now"] == "2026-11-11T15:07:00Z"
    after = await advance(u3, m["id"], "scorecard")
    assert after["section_started_at"] == "2026-11-11T15:07:00Z"


async def test_rating_rules(login_as: LoginAs) -> None:
    u2, u3, u4, u5 = [await login_as(u) for u in ("u2", "u3", "u4", "u5")]
    m = await start(u3)
    for c in (u2, u5):
        await c.post(f"{BASE}/{m['id']}/join")
    rate = f"{BASE}/{m['id']}/rating"

    early = await u2.put(rate, json={"rating": 8})
    assert (early.status_code, early.json()["code"]) == (409, "rating_not_open")
    await advance(u3, m["id"], "scorecard")
    await advance(u3, m["id"], "ids")

    assert (await u5.put(rate, json={"rating": 8})).status_code == 403  # Observer
    not_joined = await u4.put(rate, json={"rating": 8})
    assert (not_joined.status_code, not_joined.json()["code"]) == (403, "not_attendee")
    for bad in (0, 11, 7.5, "x"):
        assert (await u2.put(rate, json={"rating": bad})).status_code == 422

    await u2.put(rate, json={"rating": 9})
    await u3.put(rate, json={"rating": 7})
    state = (await u2.put(rate, json={"rating": 8})).json()["meeting"]  # changed
    assert {r["user_id"]: r["rating"] for r in state["ratings"]} == {"u2": 8, "u3": 7}
    assert state["average_rating"] == 7.5


async def test_full_meeting_and_frozen_summary(login_as: LoginAs, clock: FrozenClock) -> None:
    u2, u3 = await login_as("u2"), await login_as("u3")
    m = await start(u3)
    mid = m["id"]
    await u2.post(f"{BASE}/{mid}/join")

    # Scorecard: Make it an Issue on an off-track cell.
    made = await u2.post("/api/teams/team_lead/scorecard/measurables/m3/weeks/2026-11-02/issue")
    assert made.status_code == 201
    await advance(u3, mid, "scorecard")

    # IDS: solve an Issue and add a follow-up To-Do.
    clock.advance(60)
    solved = (
        await u2.post("/api/teams/team_lead/issues/i2/solve", json={"note": "Exec call"})
    ).json()
    assert solved["solved_in_meeting_id"] == mid
    todo = (
        await u3.post(
            "/api/teams/team_lead/issues/i2/todos", json={"title": "Follow up", "owner_id": "u2"}
        )
    ).json()
    assert todo["created_in_meeting_id"] == mid
    await advance(u3, mid, "ids")

    # Conclude: rate, end.
    await u2.put(f"{BASE}/{mid}/rating", json={"rating": 9})
    await u3.put(f"{BASE}/{mid}/rating", json={"rating": 8})
    ended = (await u3.post(f"{BASE}/{mid}/end")).json()["meeting"]
    assert ended["ended_at"] == "2026-11-11T15:01:00Z"
    assert (await u3.get(f"{BASE}/active")).json()["meeting"] is None

    summary = (await u2.get(f"{BASE}/{mid}/summary")).json()
    assert summary["scorecard_week"] == "2026-11-02"
    assert {x["id"]: x["status"] for x in summary["measurables"]} == {
        "m1": "off_track", "m2": "on_track", "m3": "off_track", "m4": "on_track", "m5": "off_track",
    }  # fmt: skip
    assert [i["id"] for i in summary["issues_solved"]] == ["i2"]
    assert [t["id"] for t in summary["todos_created"]] == [todo["id"]]
    assert [a["id"] for a in summary["attendees"]] == ["u2", "u3"]
    assert summary["average_rating"] == 8.5

    # Later edits do not change the frozen summary.
    await u2.put(
        "/api/teams/team_lead/scorecard/measurables/m1/weeks/2026-11-02", json={"value": 99}
    )
    again = (await u2.get(f"{BASE}/{mid}/summary")).json()
    assert again == summary

    # Ended meeting is closed for business.
    late = await u2.put(f"{BASE}/{mid}/rating", json={"rating": 1})
    assert (late.status_code, late.json()["code"]) == (409, "meeting_ended")
    assert (await u2.post(f"{BASE}/{mid}/join")).status_code == 409
    assert mid in [x["id"] for x in (await u2.get(BASE)).json()]


async def test_seeded_meeting_summaries(login_as: LoginAs) -> None:
    u5 = await login_as("u5")  # Observers can read summaries
    mt1 = (await u5.get(f"{BASE}/mt1/summary")).json()
    mt2 = (await u5.get(f"{BASE}/mt2/summary")).json()
    assert (mt1["scorecard_week"], mt2["scorecard_week"]) == ("2026-10-19", "2026-10-26")
    assert [i["id"] for i in mt1["issues_solved"]] == ["i7"]
    assert [t["id"] for t in mt2["todos_created"]] == ["t30"]
    assert (mt1["average_rating"], mt2["average_rating"]) == (8.0, 8.3)
    assert [a["id"] for a in mt2["attendees"]] == ["u1", "u2", "u3", "u4", "u5"]


async def test_summary_of_active_meeting_is_refused(login_as: LoginAs) -> None:
    u3 = await login_as("u3")
    m = await start(u3)
    r = await u3.get(f"{BASE}/{m['id']}/summary")
    assert (r.status_code, r.json()["code"]) == (409, "meeting_not_ended")


async def test_other_teams_meeting_is_404(login_as: LoginAs) -> None:
    u6 = await login_as("u6")  # team_sales only
    r = await u6.get("/api/teams/team_sales/meetings/mt1/summary")
    assert (r.status_code, r.json()["code"]) == (404, "meeting_not_found")
