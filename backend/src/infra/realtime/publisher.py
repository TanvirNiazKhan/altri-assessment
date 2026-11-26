from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.shared.events import EventPublisher, TeamEvent
from src.infra.realtime.codec import CHANNEL, encode


class PgEventPublisher(EventPublisher):
    """pg_notify inside the caller's transaction: Postgres delivers it only on commit,
    to every API process LISTENing, so all workers fan out the same events."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def publish(self, event: TeamEvent) -> None:
        await self._s.execute(
            text("SELECT pg_notify(:channel, :payload)"),
            {"channel": CHANNEL, "payload": encode(event)},
        )


class NullEventPublisher(EventPublisher):
    """For offline work (seed, rules report): nobody is listening."""

    async def publish(self, event: TeamEvent) -> None:
        return None
