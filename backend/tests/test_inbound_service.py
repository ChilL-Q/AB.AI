"""Service-level tests for the inbound webhook pipeline."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.client import Client
from app.db.models.conversation import Conversation
from app.db.models.team import Team
from app.services import inbound_service


@pytest.mark.asyncio
async def test_record_inbound_creates_client_and_thread(session: AsyncSession, team: Team):
    msg = await inbound_service.record_inbound_message(
        team_slug=team.slug,
        channel="whatsapp",
        phone="+77010001122",
        text="Здравствуйте",
        client_name="Айжан",
        session=session,
    )
    assert msg.direction == "inbound"
    assert msg.sent_by == "system"

    client = await session.scalar(select(Client).where(Client.team_id == team.id))
    assert client is not None
    assert client.phone == "+77010001122"
    assert client.source == "whatsapp"

    conv = await session.scalar(select(Conversation).where(Conversation.team_id == team.id))
    assert conv is not None
    assert conv.channel == "whatsapp"
    assert conv.last_message_at is not None


@pytest.mark.asyncio
async def test_record_inbound_is_idempotent_by_external_id(session: AsyncSession, team: Team):
    first = await inbound_service.record_inbound_message(
        team_slug=team.slug,
        channel="whatsapp",
        phone="+77010001122",
        text="a",
        external_id="wamid.ABC",
        session=session,
    )
    second = await inbound_service.record_inbound_message(
        team_slug=team.slug,
        channel="whatsapp",
        phone="+77010001122",
        text="a",
        external_id="wamid.ABC",
        session=session,
    )
    assert first.id == second.id


@pytest.mark.asyncio
async def test_record_inbound_rejects_unknown_team(session: AsyncSession):
    with pytest.raises(NotFoundError):
        await inbound_service.record_inbound_message(
            team_slug="no-such-team",
            channel="whatsapp",
            phone="+77010001122",
            text="a",
            session=session,
        )
