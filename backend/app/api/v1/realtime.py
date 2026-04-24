"""
WebSocket endpoint for real-time events.

Auth: JWT via `?token=<access_token>` query param — browsers can't attach
custom headers to `new WebSocket(url)`, so the token rides in the URL. We
validate it once at connect-time and never trust anything from the socket
afterwards for authorization (team_id comes from the JWT, not the client).

Protocol:
  - Server → client: RealtimeEvent JSON frames for the authenticated team.
  - Client → server: typing events, e.g. {"type": "typing.start",
    "conversation_id": "<uuid>"}. Typing events are published back to the
    team channel so other operators in the same team see them.
  - Heartbeat: server sends {"type": "ping"} every ~25s; client replies
    {"type": "pong"}. Any frame resets the idle timer.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.models.user import User
from app.db.session import get_session
from app.realtime.bus import bus
from app.realtime.events import RealtimeEvent

logger = logging.getLogger(__name__)

router = APIRouter()

HEARTBEAT_INTERVAL_SECONDS = 25


async def _resolve_user(token: str) -> User | None:
    """Decode the token and load the active user row. Returns None if any
    step fails — caller closes the socket."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        return None

    session_gen = get_session()
    session: AsyncSession = await session_gen.__anext__()
    try:
        res = await session.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return res.scalar_one_or_none()
    finally:
        await session_gen.aclose()


@router.websocket("/ws")
async def realtime_ws(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    user = await _resolve_user(token)
    if user is None or user.team_id is None:
        await websocket.close(code=4403)
        return
    team_id = user.team_id
    user_id = user.id

    await websocket.accept()

    # Announce presence to the team (best-effort; not consumed anywhere critical).
    await bus.publish(
        RealtimeEvent(
            type="presence.online",
            team_id=team_id,
            user_id=user_id,
            ts=datetime.now(UTC),
        )
    )

    async def pump_from_bus() -> None:
        async with bus.subscribe(team_id) as events:
            async for event in events:
                # Don't echo our own typing back to us.
                if event.type in ("typing.start", "typing.stop") and event.user_id == user_id:
                    continue
                await websocket.send_text(event.model_dump_json())

    async def pump_from_client() -> None:
        while True:
            try:
                raw = await asyncio.wait_for(
                    websocket.receive_text(), timeout=HEARTBEAT_INTERVAL_SECONDS * 2
                )
            except TimeoutError:
                # Client went silent past two heartbeat intervals — close.
                raise WebSocketDisconnect(code=1001) from None
            try:
                msg = RealtimeEvent.model_validate_json(raw)
            except Exception:  # noqa: BLE001
                # Allow simple pong frames that aren't full RealtimeEvents.
                if raw == "pong" or "pong" in raw:
                    continue
                continue
            # Only typing events are client-initiated right now. Everything
            # else is server-authoritative.
            if msg.type not in ("typing.start", "typing.stop"):
                continue
            await bus.publish(
                RealtimeEvent(
                    type=msg.type,
                    team_id=team_id,
                    conversation_id=msg.conversation_id,
                    user_id=user_id,
                    ts=datetime.now(UTC),
                )
            )

    async def heartbeat() -> None:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            await websocket.send_text('{"type":"ping"}')

    tasks = [
        asyncio.create_task(pump_from_bus()),
        asyncio.create_task(pump_from_client()),
        asyncio.create_task(heartbeat()),
    ]
    try:
        # First task to finish (disconnect, error, timeout) unwinds the rest.
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        # Retrieve exceptions from BOTH done and pending tasks to silence
        # "Task exception was never retrieved" warnings. Disconnects here are
        # normal lifecycle, not errors.
        await asyncio.gather(*tasks, return_exceptions=True)
        for t in done:
            exc = t.exception()
            if exc and not isinstance(exc, WebSocketDisconnect | asyncio.CancelledError):
                logger.exception("Realtime WS task failed (user=%s)", user_id, exc_info=exc)
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error in WS loop (user=%s)", user_id)
    finally:
        await bus.publish(
            RealtimeEvent(
                type="presence.offline",
                team_id=team_id,
                user_id=user_id,
                ts=datetime.now(UTC),
            )
        )
        with contextlib.suppress(Exception):
            await websocket.close()
