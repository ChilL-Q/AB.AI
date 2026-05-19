"""Smoke tests for the Redis Pub/Sub event bus.

These require a real Redis (the same REDIS_URL used in CI). If Redis is
not reachable the test is skipped — we don't want to block local runs
that don't have Redis up.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
import redis.asyncio as redis

from app.core.config import settings
from app.realtime.bus import EventBus
from app.realtime.events import RealtimeEvent


async def _redis_available() -> bool:
    try:
        r = redis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        await r.close()
        return True
    except Exception:  # noqa: BLE001
        return False


@pytest.mark.asyncio
async def test_publish_subscribe_roundtrip() -> None:
    if not await _redis_available():
        pytest.skip("Redis not available")

    bus = EventBus(settings.redis_url)
    team_id = uuid.uuid4()
    sent = RealtimeEvent(
        type="message.new",
        team_id=team_id,
        conversation_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        payload={"hello": "world"},
        ts=datetime.now(UTC),
    )

    received: list[RealtimeEvent] = []

    async def reader() -> None:
        async with bus.subscribe(team_id) as events:
            async for ev in events:
                received.append(ev)
                return

    task = asyncio.create_task(reader())
    # Give the subscriber time to actually register on the channel before
    # we publish; Redis drops messages for non-subscribed channels.
    await asyncio.sleep(0.2)
    await bus.publish(sent)
    try:
        await asyncio.wait_for(task, timeout=2.0)
    finally:
        await bus.close()

    assert len(received) == 1
    got = received[0]
    assert got.type == sent.type
    assert got.team_id == sent.team_id
    assert got.conversation_id == sent.conversation_id
    assert got.payload == sent.payload


@pytest.mark.asyncio
async def test_team_isolation() -> None:
    """Events on one team channel must not leak to another."""
    if not await _redis_available():
        pytest.skip("Redis not available")

    bus = EventBus(settings.redis_url)
    team_a = uuid.uuid4()
    team_b = uuid.uuid4()
    received_b: list[RealtimeEvent] = []

    async def reader_b() -> None:
        async with bus.subscribe(team_b) as events:
            async for ev in events:
                received_b.append(ev)
                return

    task = asyncio.create_task(reader_b())
    await asyncio.sleep(0.2)
    await bus.publish(
        RealtimeEvent(
            type="message.new",
            team_id=team_a,
            ts=datetime.now(UTC),
        )
    )
    # Give it a moment; team_b reader should not receive anything.
    try:
        await asyncio.wait_for(task, timeout=0.8)
    except TimeoutError:
        pass
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await bus.close()

    assert received_b == []
