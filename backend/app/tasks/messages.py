"""Celery tasks for the messaging pipeline.

Currently: AI-agent auto-reply orchestration. Triggered by the inbound
webhook pipeline via `.delay()`, runs out-of-band so the webhook HTTP
response stays fast.

Celery tasks are sync entry points; we bridge to the async stack with
`asyncio.run` per invocation. That's fine for a low-throughput background
queue — each task opens its own short-lived event loop and DB session.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.db.models.client import Client
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.session import AsyncSessionFactory
from app.realtime.bus import publish_nowait
from app.realtime.events import RealtimeEvent
from app.schemas.conversation import MessageOut
from app.services.ai_agent_service import AIAgentError, generate_reply, get_config
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

ESCALATION_PHRASES = [
    "поговорить с человеком",
    "позвать менеджера",
    "поговорить с менеджером",
    "соедините с оператором",
    "хочу поговорить с живым",
    "позови человека",
    "позови менеджера",
    "переключите на оператора",
    "живой человек",
    "оператор",
]


def _wants_human(text: str | None) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(phrase in lower for phrase in ESCALATION_PHRASES)


async def _run_inbound_ai_flow(conversation_id: uuid.UUID, team_id: uuid.UUID) -> None:
    """Decide what to do with an inbound message based on the team's AI mode.

    - manual:     no-op
    - semi_auto:  generate a draft, publish ai.suggestion (don't persist)
    - auto:       generate a reply, persist as Message(sent_by=ai), publish message.new
    - is_active=False: no-op (owner paused AI)
    """
    async with AsyncSessionFactory() as session:
        try:
            cfg = await get_config(team_id, session)
            if cfg.mode == "manual" or not cfg.is_active:
                return

            conv = await session.scalar(select(Conversation).where(Conversation.id == conversation_id))
            if conv and conv.status == "escalated":
                return

            last_inbound = await session.scalar(
                select(Message)
                .where(
                    Message.conversation_id == conversation_id,
                    Message.direction == "inbound",
                )
                .order_by(Message.created_at.desc())
                .limit(1)
            )

            if last_inbound and _wants_human(last_inbound.text):
                if conv:
                    conv.status = "escalated"
                    await session.commit()
                publish_nowait(
                    RealtimeEvent(
                        type="message.new",
                        team_id=team_id,
                        conversation_id=conversation_id,
                        payload={
                            "escalation": True,
                            "message": "Клиент просит поговорить с человеком",
                        },
                        ts=datetime.now(UTC),
                    )
                )
                return

            try:
                text = await generate_reply(
                    conversation_id=conversation_id, team_id=team_id, session=session
                )
            except AIAgentError as exc:
                logger.warning(
                    "AI reply skipped (conv=%s, team=%s): %s",
                    conversation_id,
                    team_id,
                    exc,
                )
                return

            if cfg.mode == "semi_auto":
                publish_nowait(
                    RealtimeEvent(
                        type="ai.suggestion",
                        team_id=team_id,
                        conversation_id=conversation_id,
                        payload={"text": text},
                        ts=datetime.now(UTC),
                    )
                )
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
            await session.refresh(msg)

            # Dispatch outbound message to the real channel
            if conv is not None:
                client = await session.scalar(select(Client).where(Client.id == conv.client_id))
                if client:
                    try:
                        from app.services.channel_dispatcher import dispatch
                        await dispatch(client.phone, client.telegram_chat_id, conv.channel, text)
                    except Exception:
                        logger.exception("Failed to dispatch AI outbound to channel")

            publish_nowait(
                RealtimeEvent(
                    type="message.new",
                    team_id=team_id,
                    conversation_id=conversation_id,
                    payload=MessageOut.model_validate(msg).model_dump(mode="json"),
                    ts=now,
                )
            )
        except Exception:
            await session.rollback()
            raise


async def _dispose_engine() -> None:
    """Dispose the SQLAlchemy async engine pool to clear stale connections."""
    from app.db.session import engine
    await engine.dispose()


@celery_app.task(name="app.tasks.messages.handle_inbound_for_ai")
def handle_inbound_for_ai(conversation_id: str, team_id: str) -> None:
    """Celery entry point — see `_run_inbound_ai_flow` for semantics.

    Uses asyncio.run() for each invocation and disposes the SQLAlchemy
    engine pool afterwards so stale asyncpg connections (bound to a
    previous loop) are not reused.
    """
    try:
        asyncio.run(_run_inbound_ai_flow(uuid.UUID(conversation_id), uuid.UUID(team_id)))
    except Exception:  # noqa: BLE001
        logger.exception("handle_inbound_for_ai crashed (conv=%s)", conversation_id)
    finally:
        try:
            asyncio.run(_dispose_engine())
        except Exception:
            pass
