import asyncio
from datetime import date
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import func, select

from src.infra.database.models import IssueModel
from tests.conftest import LoginAs

pytestmark = pytest.mark.db

CELL = "/api/teams/team_lead/scorecard/measurables/{m}/weeks/{w}"


def cell_of(scorecard: dict[str, Any], measurable_id: str, week: str) -> dict[str, Any]:
    row = next(r for r in scorecard["rows"] if r["id"] == measurable_id)
    cell: dict[str, Any] = next(c for c in row["cells"] if c["week_start"] == week)
    return cell


async def test_scorecard_has_13_weeks_with_statuses(login_as: LoginAs) -> None:
    u2 = await login_as("u2")
    sc = (await u2.get("/api/teams/team_lead/scorecard")).json()
    assert len(sc["weeks"]) == 13
    assert (sc["weeks"][0], sc["weeks"][-1], sc["current_week"]) == (
        "2026-08-17",
        "2026-11-09",
        "2026-11-09",
    )
    assert [r["id"] for r in sc["rows"]] == ["m1", "m2", "m3", "m4", "m5"]
    m1 = sc["rows"][0]
    assert m1["owner"]["name"] and m1["goal"] == {
        "type": "at_least",
        "value": 10.0,
        "min": None,
        "max": None,
    }
    assert cell_of(sc, "m2", "2026-09-07")["status"] == "on_track"
    assert cell_of(sc, "m5", "2026-11-02") == {
        "week_start": "2026-11-02",
        "value": None,
        "status": "off_track",
        "open_issue_id": None,
    }
    assert cell_of(sc, "m1", "2026-11-09")["status"] == "pending"
    assert cell_of(sc, "m1", "2026-11-02")["open_issue_id"] == "i5"


async def test_edit_score_last_save_wins_and_status_follows(login_as: LoginAs) -> None:
    u2, u3 = await login_as("u2"), await login_as("u3")
    url = CELL.format(m="m1", w="2026-11-09")
    r = await u2.put(url, json={"value": 12})
    assert r.json() == {
        "week_start": "2026-11-09",
        "value": 12.0,
        "status": "on_track",
        "open_issue_id": None,
    }
    await u3.put(url, json={"value": 3.5})
    sc = (await u2.get("/api/teams/team_lead/scorecard")).json()
    assert cell_of(sc, "m1", "2026-11-09")["value"] == 3.5
    assert cell_of(sc, "m1", "2026-11-09")["status"] == "off_track"
    await u2.put(url, json={"value": None})
    sc = (await u2.get("/api/teams/team_lead/scorecard")).json()
    assert cell_of(sc, "m1", "2026-11-09")["status"] == "pending"


@pytest.mark.parametrize(
    ("week", "body", "code"),
    [
        ("2026-11-16", {"value": 1}, "invalid_week"),  # future
        ("2026-08-10", {"value": 1}, "invalid_week"),  # older than the 13-week window
        ("2026-11-10", {"value": 1}, "invalid_week"),  # not a Monday
        ("2026-11-09", {"value": "abc"}, "validation_error"),
        ("2026-11-09", {"value": 1.23456}, "validation_error"),
        ("2026-11-09", {}, "validation_error"),
        ("2026-11-09", {"value": 1, "extra": True}, "validation_error"),
        ("not-a-date", {"value": 1}, "validation_error"),
    ],
)
async def test_score_input_is_validated(
    login_as: LoginAs, week: str, body: dict[str, object], code: str
) -> None:
    u2 = await login_as("u2")
    r = await u2.put(CELL.format(m="m1", w=week), json=body)
    assert (r.status_code, r.json()["code"]) == (422, code)


async def test_make_it_an_issue_creates_then_returns_existing(login_as: LoginAs) -> None:
    u2, u3 = await login_as("u2"), await login_as("u3")
    url = CELL.format(m="m1", w="2026-10-26") + "/issue"
    first = await u2.post(url)
    assert first.status_code == 201
    issue = first.json()
    assert issue["title"] == "New deals closed, week of Oct 26"
    assert issue["owner"]["id"] == "u2" and issue["priority"] is None
    assert issue["source"] == {
        "type": "measurable",
        "measurable_id": "m1",
        "measurable_name": "New deals closed",
        "week_start": "2026-10-26",
        "rock_id": None,
    }
    second = await u3.post(url)
    assert (second.status_code, second.json()["id"]) == (200, issue["id"])


async def test_make_it_an_issue_returns_seeded_unsolved_issue(login_as: LoginAs) -> None:
    u3 = await login_as("u3")
    r = await u3.post(CELL.format(m="m1", w="2026-11-02") + "/issue")
    assert (r.status_code, r.json()["id"]) == (200, "i5")


async def test_make_it_an_issue_after_solving_creates_a_new_one(login_as: LoginAs) -> None:
    """i6 (m4, Oct 26) is solved, so the slot is free again."""
    u2 = await login_as("u2")
    r = await u2.post(CELL.format(m="m4", w="2026-10-26") + "/issue")
    assert r.status_code == 201 and r.json()["id"] != "i6"


@pytest.mark.parametrize(
    ("measurable", "week"),
    [("m1", "2026-09-07"), ("m1", "2026-11-09")],  # on track; pending (current week)
)
async def test_make_it_an_issue_requires_off_track(
    login_as: LoginAs, measurable: str, week: str
) -> None:
    u2 = await login_as("u2")
    r = await u2.post(CELL.format(m=measurable, w=week) + "/issue")
    assert (r.status_code, r.json()["code"]) == (422, "not_off_track")


async def test_concurrent_make_it_an_issue_returns_one_issue(
    app: FastAPI, login_as: LoginAs
) -> None:
    """20 simultaneous clicks from 4 users -> exactly one Issue, one 201, same id everywhere."""
    clients = [await login_as(u) for u in ("u1", "u2", "u3", "u4")]
    url = CELL.format(m="m3", w="2026-11-02") + "/issue"
    responses = await asyncio.gather(*(clients[i % 4].post(url) for i in range(20)))

    statuses = sorted(r.status_code for r in responses)
    assert statuses == [200] * 19 + [201]
    assert len({r.json()["id"] for r in responses}) == 1

    async with app.state.sessionmaker() as session:
        count = await session.scalar(
            select(func.count())
            .select_from(IssueModel)
            .where(
                IssueModel.source_measurable_id == "m3",
                IssueModel.source_week_start == date(2026, 11, 2),
            )
        )
    assert count == 1


async def test_open_issue_shows_on_scorecard_cell(login_as: LoginAs, client: AsyncClient) -> None:
    u2 = await login_as("u2")
    issue = (await u2.post(CELL.format(m="m2", w="2026-08-31") + "/issue")).json()
    sc = (await u2.get("/api/teams/team_lead/scorecard")).json()
    assert cell_of(sc, "m2", "2026-08-31")["open_issue_id"] == issue["id"]
