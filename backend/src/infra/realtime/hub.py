"""In-process registry of live connections per team (one per API worker)."""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Protocol

log = logging.getLogger(__name__)


class Subscriber(Protocol):
    async def send_json(self, data: Any) -> None: ...


class ConnectionHub:
    def __init__(self) -> None:
        self._subs: defaultdict[str, set[Subscriber]] = defaultdict(set)

    def add(self, team_id: str, sub: Subscriber) -> None:
        self._subs[team_id].add(sub)

    def remove(self, team_id: str, sub: Subscriber) -> None:
        subs = self._subs.get(team_id)
        if subs is not None:
            subs.discard(sub)
            if not subs:
                del self._subs[team_id]

    def teams(self) -> list[str]:
        return list(self._subs)

    def count(self, team_id: str) -> int:
        return len(self._subs.get(team_id, ()))

    async def broadcast(self, team_id: str, message: dict[str, Any]) -> None:
        subs = list(self._subs.get(team_id, ()))
        results = await asyncio.gather(
            *(s.send_json(message) for s in subs), return_exceptions=True
        )
        for sub, result in zip(subs, results, strict=True):
            if isinstance(result, Exception):
                log.info("dropping dead subscriber on %s: %r", team_id, result)
                self.remove(team_id, sub)
