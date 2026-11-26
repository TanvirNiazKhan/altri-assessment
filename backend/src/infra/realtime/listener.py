"""LISTEN on the team-events channel with automatic reconnect.

After a reconnect, notifications sent while disconnected are lost, so `on_reconnect` is
called to let the app push fresh state to every connected client.
"""

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

import asyncpg

from src.domain.shared.events import TeamEvent
from src.infra.realtime.codec import CHANNEL, decode

log = logging.getLogger(__name__)

EventHandler = Callable[[TeamEvent], Coroutine[Any, Any, None]]
ReconnectHandler = Callable[[], Awaitable[None]]


def asyncpg_dsn(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.replace("postgresql+asyncpg://", "postgresql://", 1)


class PgListener:
    def __init__(
        self,
        dsn: str,
        on_event: EventHandler,
        on_reconnect: ReconnectHandler | None = None,
        *,
        max_backoff_s: float = 5.0,
    ) -> None:
        self._dsn = dsn
        self._on_event = on_event
        self._on_reconnect = on_reconnect
        self._max_backoff_s = max_backoff_s
        self._task: asyncio.Task[None] | None = None
        self._handlers: set[asyncio.Task[None]] = set()
        self.ready = asyncio.Event()

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name="pg-listener")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        for t in list(self._handlers):
            t.cancel()

    async def _run(self) -> None:
        backoff, connected_before = 0.5, False
        while True:
            conn: asyncpg.Connection | None = None
            try:
                conn = await asyncpg.connect(self._dsn)
                lost = asyncio.Event()
                conn.add_termination_listener(lambda _c, _lost=lost: _lost.set())
                await conn.add_listener(CHANNEL, self._notify)
                self.ready.set()
                backoff = 0.5
                if connected_before and self._on_reconnect:
                    await self._on_reconnect()
                connected_before = True
                await lost.wait()
                log.warning("LISTEN connection lost; reconnecting")
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("LISTEN connection failed; retrying in %.1fs", backoff)
            finally:
                self.ready.clear()
                if conn is not None and not conn.is_closed():
                    await conn.close()
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, self._max_backoff_s)

    def _notify(self, _conn: object, _pid: int, _channel: str, payload: str) -> None:
        try:
            event = decode(payload)
        except (ValueError, KeyError):
            log.warning("ignoring malformed team event: %s", payload[:200])
            return
        task: asyncio.Task[None] = asyncio.create_task(self._on_event(event))
        self._handlers.add(task)
        task.add_done_callback(self._handlers.discard)
