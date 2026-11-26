"""Real-time sync over a real server: uvicorn on a random port, real WebSockets, and the
Postgres NOTIFY fan-out path end to end."""

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import pytest
import uvicorn
from fastapi import FastAPI
from httpx import AsyncClient
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import InvalidStatus

from src.config.settings import Settings
from src.infra.services.clock import FrozenClock
from src.main import create_app

pytestmark = pytest.mark.db
TIMEOUT_S = 3.0


@dataclass
class LiveServer:
    app: FastAPI
    http: str
    ws: str

    def cookie(self, user_id: str) -> str:
        return f"l10_session={self.app.state.session_signer.sign(user_id)}"

    def client(self, user_id: str) -> AsyncClient:
        return AsyncClient(base_url=self.http, headers={"Cookie": self.cookie(user_id)})

    def socket(self, user_id: str, team_id: str = "team_lead") -> Any:
        return connect(
            f"{self.ws}/api/ws/teams/{team_id}",
            additional_headers={"Cookie": self.cookie(user_id)},
        )


@pytest.fixture
async def live(settings: Settings, clock: FrozenClock) -> AsyncIterator[LiveServer]:
    app = create_app(settings, clock)
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning", lifespan="on")
    )
    task = asyncio.create_task(server.serve())
    while not server.started:  # noqa: ASYNC110 - uvicorn exposes no "started" event
        await asyncio.sleep(0.02)
    await asyncio.wait_for(app.state.listener.ready.wait(), TIMEOUT_S)
    port = server.servers[0].sockets[0].getsockname()[1]
    yield LiveServer(app=app, http=f"http://127.0.0.1:{port}", ws=f"ws://127.0.0.1:{port}")
    server.should_exit = True
    await task


async def next_message(ws: ClientConnection, type_: str) -> dict[str, Any]:
    """Next message of `type_` (skipping others), or fail after TIMEOUT_S."""

    async def wait() -> dict[str, Any]:
        while True:
            msg: dict[str, Any] = json.loads(await ws.recv())
            if msg["type"] == type_:
                return msg

    return await asyncio.wait_for(wait(), TIMEOUT_S)


async def test_snapshot_on_connect(live: LiveServer) -> None:
    async with live.socket("u2") as ws:
        first = await next_message(ws, "meeting.state")
        assert first["data"]["meeting"] is None
        assert first["data"]["server_now"].startswith("2026-11-11T15:00:00")


async def test_second_browser_follows_facilitator(live: LiveServer) -> None:
    """Facilitator advances; the other attendee's socket receives each new section."""
    async with (
        live.client("u3") as facilitator,
        live.client("u2") as member,
        live.socket("u3") as ws_fac,
        live.socket("u2") as ws_member,
    ):
        for ws in (ws_fac, ws_member):
            await next_message(ws, "meeting.state")  # connect snapshot

        mid = (await facilitator.post("/api/teams/team_lead/meetings")).json()["meeting"]["id"]
        for ws in (ws_member, ws_fac):
            started = await next_message(ws, "meeting.state")
            assert started["data"]["meeting"]["current_section"] == "scorecard"

        await member.post(f"/api/teams/team_lead/meetings/{mid}/join")
        for ws in (ws_member, ws_fac):
            joined = await next_message(ws, "meeting.state")
            assert {a["id"] for a in joined["data"]["meeting"]["attendees"]} == {"u2", "u3"}

        for expected, nxt in (("scorecard", "ids"), ("ids", "conclude")):
            r = await facilitator.post(
                f"/api/teams/team_lead/meetings/{mid}/advance",
                json={"expected_section": expected},
            )
            assert r.status_code == 200
            for ws in (ws_member, ws_fac):
                msg = await next_message(ws, "meeting.state")
                assert msg["data"]["meeting"]["current_section"] == nxt

        await facilitator.post(f"/api/teams/team_lead/meetings/{mid}/end")
        ended = await next_message(ws_member, "meeting.state")
        assert ended["data"]["meeting"]["ended_at"] is not None


async def test_late_join_recovers_current_state(live: LiveServer) -> None:
    async with live.client("u3") as facilitator:
        mid = (await facilitator.post("/api/teams/team_lead/meetings")).json()["meeting"]["id"]
        await facilitator.post(
            f"/api/teams/team_lead/meetings/{mid}/advance", json={"expected_section": "scorecard"}
        )
        async with live.socket("u5") as ws:  # Observer connects mid-meeting
            snap = await next_message(ws, "meeting.state")
            assert snap["data"]["meeting"]["id"] == mid
            assert snap["data"]["meeting"]["current_section"] == "ids"


async def test_data_changes_are_pushed(live: LiveServer) -> None:
    async with live.client("u2") as u2, live.socket("u5") as ws:
        await next_message(ws, "meeting.state")
        await u2.post("/api/teams/team_lead/issues", json={"title": "Live issue"})
        assert (await next_message(ws, "data.changed"))["resources"] == ["issues"]
        await u2.put("/api/teams/team_lead/todos/t12/done")
        assert (await next_message(ws, "data.changed"))["resources"] == ["todos"]


async def test_events_stay_within_the_team(live: LiveServer) -> None:
    async with live.client("u6") as sales, live.socket("u5") as lead_ws:
        await next_message(lead_ws, "meeting.state")
        await sales.post("/api/teams/team_sales/issues", json={"title": "Sales only"})
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(lead_ws.recv(), 0.5)


async def test_ping_pong(live: LiveServer) -> None:
    async with live.socket("u2") as ws:
        await next_message(ws, "meeting.state")
        await ws.send("ping")
        assert "server_now" in await next_message(ws, "pong")


@pytest.mark.parametrize(("user", "team"), [("u2", "team_ops"), (None, "team_lead")])
async def test_socket_requires_access(live: LiveServer, user: str | None, team: str) -> None:
    headers = {"Cookie": live.cookie(user)} if user else {}
    with pytest.raises(InvalidStatus) as rejected:
        async with connect(f"{live.ws}/api/ws/teams/{team}", additional_headers=headers):
            pass
    assert rejected.value.response.status_code == 403
