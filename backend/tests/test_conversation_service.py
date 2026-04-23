"""
Smoke tests for conversation_service covering the mutation and listing
paths surfaced in the API. Runs against the real Postgres in CI via
conftest.engine (schema recreated once per session, rolled back per test).
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.client import Client
from app.db.models.message import Message
from app.db.models.team import Team
from app.db.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
)
from app.services import conversation_service


@pytest.mark.asyncio
async def test_create_conversation_is_idempotent(
    session: AsyncSession, team: Team, client: Client
):
    payload = ConversationCreate(client_id=client.id, channel="whatsapp")
    first = await conversation_service.create_conversation(team.id, payload, session)
    second = await conversation_service.create_conversation(team.id, payload, session)
    assert first.id == second.id, "Same (client, channel, active) should return the same thread"


@pytest.mark.asyncio
async def test_send_message_creates_outbound_and_bumps_last_message_at(
    session: AsyncSession, team: Team, user: User, client: Client
):
    conv = await conversation_service.create_conversation(
        team.id, ConversationCreate(client_id=client.id, channel="whatsapp"), session
    )
    assert conv.last_message_at is None

    msg = await conversation_service.send_message(
        team.id, conv.id, user.id, MessageCreate(text="Здравствуйте!"), session
    )
    assert msg.direction == "outbound"
    assert msg.sent_by == "human"
    assert msg.status == "sent"
    assert msg.user_id == user.id
    assert msg.sent_at is not None

    refreshed = await conversation_service.get_conversation(team.id, conv.id, session)
    assert refreshed.last_message_at is not None


@pytest.mark.asyncio
async def test_list_conversations_preview_falls_back_for_media_only(
    session: AsyncSession, team: Team, client: Client
):
    conv = await conversation_service.create_conversation(
        team.id, ConversationCreate(client_id=client.id, channel="telegram"), session
    )
    session.add(
        Message(
            conversation_id=conv.id,
            direction="inbound",
            text=None,
            media_url="https://cdn.example/photo.jpg",
            status="delivered",
            sent_by="system",
        )
    )
    await session.flush()

    page = await conversation_service.list_conversations(team.id, session)
    [row] = [c for c in page.data if c.id == conv.id]
    assert row.last_message_preview == "[вложение]"


@pytest.mark.asyncio
async def test_update_conversation_can_switch_channel_and_status(
    session: AsyncSession, team: Team, client: Client
):
    conv = await conversation_service.create_conversation(
        team.id, ConversationCreate(client_id=client.id, channel="whatsapp"), session
    )
    updated = await conversation_service.update_conversation(
        team.id, conv.id, ConversationUpdate(channel="telegram", status="resolved"), session
    )
    assert updated.channel == "telegram"
    assert updated.status == "resolved"


@pytest.mark.asyncio
async def test_list_by_client_scopes_to_team(
    session: AsyncSession, team: Team, client: Client
):
    await conversation_service.create_conversation(
        team.id, ConversationCreate(client_id=client.id, channel="whatsapp"), session
    )
    await conversation_service.create_conversation(
        team.id, ConversationCreate(client_id=client.id, channel="telegram"), session
    )
    rows = await conversation_service.list_conversations_by_client(team.id, client.id, session)
    assert len(rows) == 2
    assert {r.channel for r in rows} == {"whatsapp", "telegram"}
