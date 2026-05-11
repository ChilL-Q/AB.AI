"""Inbound webhook pipeline.

Handles messages coming in from external messengers. Upserts the client
by (team, phone), finds-or-creates an active conversation for the given
channel, inserts the inbound message, and bumps last_message_at.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.client import Client
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.outreach_attempt import OutreachAttempt
from app.db.models.team import Team
from app.db.session import AsyncSessionFactory
from app.realtime.bus import publish_nowait
from app.realtime.events import RealtimeEvent
from app.schemas.conversation import MessageOut

logger = logging.getLogger(__name__)


async def record_inbound_message(
    *,
    team_slug: str,
    channel: Literal["whatsapp", "telegram", "sms"],
    phone: str,
    text: str | None,
    media_url: str | None = None,
    client_name: str | None = None,
    external_id: str | None = None,
    telegram_chat_id: str | None = None,
    telegram_username: str | None = None,
    session: AsyncSession | None = None,
) -> Message:
    own_session = session is None
    if own_session:
        session = AsyncSessionFactory()

    try:
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
                telegram_chat_id=telegram_chat_id,
                telegram_username=telegram_username,
            )
            session.add(client)
            await session.flush()

        if telegram_chat_id and not client.telegram_chat_id:
            client.telegram_chat_id = telegram_chat_id
        if telegram_username and not client.telegram_username:
            client.telegram_username = telegram_username

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

        # Mark any pending outreach attempt for this conversation as replied.
        outreach = await session.scalar(
            select(OutreachAttempt).where(
                OutreachAttempt.conversation_id == conv.id,
                OutreachAttempt.status == "sent",
                OutreachAttempt.replied_at.is_(None),
            )
        )
        if outreach:
            outreach.status = "replied"
            outreach.replied_at = now
            await session.flush()

        # Handle /stop — opt out of proactive outreach
        if text and text.strip().lower() in ("/stop", "/stop", "стоп"):
            client.do_not_contact = True
            await session.flush()

        # Commit immediately so that row locks are released before we dispatch
        # the Celery task.  Without this, the uncommitted transaction holds an
        # ExclusiveLock on the conversation row, which blocks the Celery
        # worker's own UPDATE on the same row.
        if own_session:
            await session.commit()
        else:
            # When the caller provides its own session (e.g. the FastAPI
            # dependency), we flush but let the caller control the commit.
            # To avoid blocking the Celery worker, we dispatch the task *after*
            # the response is sent (see webhook handler).
            pass

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

        # Enqueue AI processing via Celery (non-blocking for the request).
        # IMPORTANT: This must run AFTER the transaction commits so the Celery
        # worker can acquire row locks on the conversation.
        import sys
        print(f"[INBOUND] About to dispatch Celery task for conv={conv.id}", file=sys.stderr, flush=True)
        from app.tasks.messages import handle_inbound_for_ai
        try:
            result = handle_inbound_for_ai.delay(str(conv.id), str(team.id))
            print(f"[INBOUND] Celery task dispatched: task_id={result.id}", file=sys.stderr, flush=True)
            logger.info("Celery task dispatched: conv=%s team=%s task_id=%s", conv.id, team.id, result.id)
        except Exception as exc:
            print(f"[INBOUND] Celery dispatch FAILED: {exc}", file=sys.stderr, flush=True)
            logger.exception("Celery unavailable, skipping AI reply for conv=%s", conv.id)

        return msg
    finally:
        if own_session:
            await session.close()


async def _run_ai_reply_inline(conversation_id, team_id) -> None:
    """Run the AI reply pipeline inline when Celery is unavailable."""
    from app.services.ai_agent_service import get_config, generate_reply, AIAgentError
    from app.db.models.client import Client
    from app.db.models.conversation import Conversation as ConvModel
    from app.db.models.message import Message

    async with AsyncSessionFactory() as session:
        cfg = await get_config(team_id, session)
        if cfg.mode == "manual" or not cfg.is_active:
            return

        conv = await session.scalar(select(ConvModel).where(ConvModel.id == conversation_id))
        if conv and conv.status == "escalated":
            return

        client = await session.scalar(select(Client).where(Client.id == conv.client_id)) if conv else None

        from app.tasks.messages import _wants_human
        last_inbound = await session.scalar(
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.direction == "inbound")
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        if last_inbound and _wants_human(last_inbound.text):
            if conv:
                conv.status = "escalated"
                await session.commit()
            return

        try:
            text = await generate_reply(conversation_id=conversation_id, team_id=team_id, session=session)
        except AIAgentError:
            return

        if cfg.mode == "semi_auto":
            return

        now = datetime.now(UTC)
        msg = Message(
            conversation_id=conversation_id,
            direction="outbound",
            text=text,
            status="sent",
            sent_by="ai",
            sent_at=now,
        )
        session.add(msg)
        if conv is not None:
            conv.last_message_at = now
        await session.commit()

        # Dispatch to real channel
        if client and conv:
            try:
                from app.services.channel_dispatcher import dispatch
                await dispatch(client.phone, client.telegram_chat_id, conv.channel, text)
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Failed to dispatch inline reply to channel")


__all__ = ["record_inbound_message"]
