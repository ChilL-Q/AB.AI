"""
Redis Pub/Sub event bus.

Why Redis, not in-process queue: in production we'll run multiple uvicorn
workers behind a load balancer. A websocket subscribed to instance A needs
to see events emitted from a webhook that landed on instance B. Redis is
the fan-out layer.

Channel layout: one channel per team — `realtime:team:{team_id}`. The WS
connection subscribes to its own team channel only; RBAC is enforced at
subscribe-time (we never accept team_id from the client).

The bus is safe to call from anywhere (async code paths). If Redis is
unreachable we log and swallow the error — real-time is best-effort and
must not break write paths.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from uuid import UUID

import redis.asyncio as redis

from app.core.config import settings
from app.realtime.events import RealtimeEvent

logger = logging.getLogger(__name__)


def _team_channel(team_id: UUID) -> str:
    return f"realtime:team:{team_id}"


class EventBus:
    """Thin wrapper over redis.asyncio pub/sub.

    Single shared publisher connection; subscribers get a dedicated PubSub
    connection each (Redis requirement).
    """

    def __init__(self, url: str) -> None:
        self._url = url
        self._publisher: redis.Redis | None = None

    async def _get_publisher(self) -> redis.Redis:
        if self._publisher is None:
            self._publisher = redis.from_url(self._url, decode_responses=True)
        return self._publisher

    async def publish(self, event: RealtimeEvent) -> None:
        try:
            pub = await self._get_publisher()
            await pub.publish(_team_channel(event.team_id), event.model_dump_json())
        except Exception:  # noqa: BLE001 — real-time is best-effort
            logger.exception("Failed to publish realtime event (type=%s)", event.type)

    @asynccontextmanager
    async def subscribe(self, team_id: UUID) -> AsyncIterator[AsyncIterator[RealtimeEvent]]:
        """Yield an async iterator of events for a single team.

        Usage:
            async with bus.subscribe(team_id) as events:
                async for event in events:
                    ...
        """
        sub_client = redis.from_url(self._url, decode_responses=True)
        pubsub = sub_client.pubsub()
        try:
            await pubsub.subscribe(_team_channel(team_id))
            yield self._iter_events(pubsub)
        finally:
            with suppress(Exception):
                await pubsub.unsubscribe(_team_channel(team_id))
            await pubsub.close()
            await sub_client.close()

    async def _iter_events(self, pubsub: redis.client.PubSub) -> AsyncIterator[RealtimeEvent]:
        while True:
            # get_message with timeout lets us cooperate with cancellation,
            # and avoids a busy loop.
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30)
            if msg is None:
                continue
            data = msg.get("data")
            if not data:
                continue
            try:
                yield RealtimeEvent.model_validate_json(data)
            except Exception:  # noqa: BLE001 — skip malformed payloads
                logger.exception("Failed to parse realtime event payload")
                continue

    async def close(self) -> None:
        if self._publisher is not None:
            with suppress(Exception):
                await self._publisher.close()
            self._publisher = None


# Process-wide singleton. Uvicorn will construct one per worker, each with
# its own Redis connection pool; Redis pub/sub fans out across workers.
bus = EventBus(settings.redis_url)


async def shutdown_bus() -> None:
    await bus.close()


def _run_background(coro) -> None:
    """Schedule a publish without awaiting, safe inside request handlers.

    Creates a task on the running loop; if no loop is running (sync context,
    e.g. Celery worker) we fall back to asyncio.run in a thread.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)


def publish_nowait(event: RealtimeEvent) -> None:
    """Fire-and-forget publish from inside async request handlers."""
    _run_background(bus.publish(event))
