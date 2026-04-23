"""Inbound webhook pipeline.

Handles messages coming in from external messengers. Upserts the client
by (team, phone), finds-or-creates an active conversation for the given
channel, inserts the inbound message, and bumps last_message_at.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.client import Client
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.team import Team
from app.realtime.bus import publish_nowait
from app.realtime.events import RealtimeEvent
from app.schemas.conversation import MessageOut


async def record_inbound_message(
    *,
    team_slug: str,
    channel: Literal["whatsapp", "telegram", "sms"],
    phone: str,
    text: str | None,
    media_url: str | None = None,
    client_name: str | None = None,
    external_id: str | None = None,
    session: AsyncSession,
) -> Message:
    team = await session.scalar(select(Team).where(Team.slug == team_slug))
    if not team:
        raise NotFoundError("Team not found")

    # Idempotency: if we've already stored this provider message, return it.
    if external_id:
        existing = await session.scalar(select(Message).where(Message.external_id == external_id))
        if existing:
            return existing

    client = await session.scalar(
        select(Client).where(
            Client.team_id == team.id,
            Client.phone == phone,
            Client.deleted_at.is_(None),
        )
    )
    if not client:
        client = Client(
            team_id=team.id,
            full_name=client_name or phone,
            phone=phone,
            source=channel,
        )
        session.add(client)
        await session.flush()

    conv = await session.scalar(
        select(Conversation).where(
            Conversation.team_id == team.id,
            Conversation.client_id == client.id,
            Conversation.channel == channel,
            Conversation.status == "active",
        )
    )
    if not conv:
        conv = Conversation(
            team_id=team.id,
            client_id=client.id,
            channel=channel,
            status="active",
        )
        session.add(conv)
        await session.flush()

    now = datetime.now(UTC)
    msg = Message(
        conversation_id=conv.id,
        direction="inbound",
        text=text,
        media_url=media_url,
        status="delivered",
        sent_by="system",
        external_id=external_id,
        sent_at=now,
    )
    session.add(msg)
    conv.last_message_at = now
    await session.flush()

    # Fan out to connected operators so open threads update live.
    publish_nowait(
        RealtimeEvent(
            type="message.new",
            team_id=team.id,
            conversation_id=conv.id,
            payload=MessageOut.model_validate(msg).model_dump(mode="json"),
            ts=now,
        )
    )
    return msg


__all__ = ["record_inbound_message"]
