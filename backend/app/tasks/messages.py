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

from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.session import AsyncSessionFactory
from app.realtime.bus import bus
from app.realtime.events import RealtimeEvent
from app.schemas.conversation import MessageOut
from app.services.ai_agent_service import AIAgentError, generate_reply, get_config
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_inbound_ai_flow(conversation_id: uuid.UUID, team_id: uuid.UUID) -> None:
    """Decide what to do with an inbound message based on the team's AI mode.

    - manual:     no-op
    - semi_auto:  generate a draft, publish ai.suggestion (don't persist)
    - auto:       generate a reply, persist as Message(sent_by=ai), publish message.new
    """
    async with AsyncSessionFactory() as session:
        cfg = await get_config(team_id, session)
        if cfg.mode == "manual":
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
            # Ephemeral: never hits the DB. UI shows a chip above the
            # composer; operator accepts or dismisses.
            await bus.publish(
                RealtimeEvent(
                    type="ai.suggestion",
                    team_id=team_id,
                    conversation_id=conversation_id,
                    payload={"text": text},
                    ts=datetime.now(UTC),
                )
            )
            return

        # auto mode — persist as an outbound AI message and broadcast.
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
        conv = await session.scalar(select(Conversation).where(Conversation.id == conversation_id))
        if conv is not None:
            conv.last_message_at = now
        await session.commit()
        await session.refresh(msg)

        await bus.publish(
            RealtimeEvent(
                type="message.new",
                team_id=team_id,
                conversation_id=conversation_id,
                payload=MessageOut.model_validate(msg).model_dump(mode="json"),
                ts=now,
            )
        )


@celery_app.task(name="app.tasks.messages.handle_inbound_for_ai")
def handle_inbound_for_ai(conversation_id: str, team_id: str) -> None:
    """Celery entry point — see `_run_inbound_ai_flow` for semantics."""
    try:
        asyncio.run(_run_inbound_ai_flow(uuid.UUID(conversation_id), uuid.UUID(team_id)))
    except Exception:  # noqa: BLE001
        # We've already logged inside the async flow; this catch is a last
        # line of defense so Celery marks the task failed without retrying
        # an expensive LLM call.
        logger.exception("handle_inbound_for_ai crashed (conv=%s)", conversation_id)
