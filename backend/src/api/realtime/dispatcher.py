"""Turns committed team events into WebSocket messages.

Message types (server -> client):
  meeting.state  {"type", "data": MeetingStateResponse}  full snapshot, apply if newer
  data.changed   {"type", "resources": [...]}             refetch those resources via REST
  pong           {"type", "server_now"}                   reply to a client "ping"
"""

import asyncio
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.schemas.meeting import MeetingStateResponse
from src.config.dependency import build_meeting_service
from src.domain.shared.clock import Clock
from src.domain.shared.events import TeamEvent, Topic
from src.domain.shared.exceptions import DomainError
from src.infra.realtime.hub import ConnectionHub
from src.infra.realtime.publisher import NullEventPublisher

log = logging.getLogger(__name__)
ALL_RESOURCES = sorted(t.value for t in Topic if t is not Topic.MEETING)


class TeamEventDispatcher:
    def __init__(
        self, hub: ConnectionHub, sessionmaker: async_sessionmaker[AsyncSession], clock: Clock
    ) -> None:
        self._hub = hub
        self._sessionmaker = sessionmaker
        self._clock = clock

    async def handle(self, event: TeamEvent) -> None:
        if not self._hub.count(event.team_id):
            return
        try:
            if Topic.MEETING in event.topics:
                message = await self.meeting_message(event.team_id, event.meeting_id)
                await self._hub.broadcast(event.team_id, message)
            resources = sorted(t.value for t in event.topics if t is not Topic.MEETING)
            if resources:
                await self._hub.broadcast(
                    event.team_id, {"type": "data.changed", "resources": resources}
                )
        except Exception:
            log.exception("failed to dispatch %s", event)

    async def meeting_message(self, team_id: str, meeting_id: str | None = None) -> dict[str, Any]:
        """Current snapshot of `meeting_id` (active or just ended) or the team's active meeting."""
        async with self._sessionmaker() as session:
            meetings = build_meeting_service(session, NullEventPublisher())
            try:
                state = (
                    await meetings.state(team_id, meeting_id)
                    if meeting_id
                    else await meetings.active_state(team_id)
                )
            except DomainError:
                state = None
        data = MeetingStateResponse.build(state, self._clock.now()).model_dump(mode="json")
        return {"type": "meeting.state", "data": data}

    async def resync_all(self) -> None:
        """After a LISTEN reconnect: events may have been missed, so push fresh state."""
        for team_id in self._hub.teams():
            await self._hub.broadcast(team_id, await self.meeting_message(team_id))
            await self._hub.broadcast(team_id, {"type": "data.changed", "resources": ALL_RESOURCES})

    def pong(self) -> dict[str, Any]:
        return {"type": "pong", "server_now": self._clock.now().isoformat()}


class SocketSubscriber:
    """Serializes sends on one socket (the dispatcher and the receive loop both send)."""

    def __init__(self, socket: Any) -> None:
        self._socket = socket
        self._lock = asyncio.Lock()

    async def send_json(self, data: Any) -> None:
        async with self._lock:
            await self._socket.send_json(data)
