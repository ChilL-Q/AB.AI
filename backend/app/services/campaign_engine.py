"""Campaign execution engine.

When a campaign is started (status → running), a Celery task picks it up and:
1. Finds matching clients based on trigger criteria
2. Renders the message template (or asks LLM if no template)
3. Creates OutreachAttempts + Messages for each recipient
4. Updates campaign stats (sent, replied, etc.)
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.ai_agent_config import AIAgentConfig
from app.db.models.campaign import Campaign
from app.db.models.client import Client
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.outreach_attempt import OutreachAttempt
from app.db.models.template import Template

logger = logging.getLogger(__name__)


def _render_template(content: str, client: Client) -> str:
    """Replace template variables with client data."""
    replacements = {
        "{name}": client.full_name,
        "{phone}": client.phone,
        "{email}": client.email or "",
    }
    result = content
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def _match_trigger(client: Client, trigger: dict) -> bool:
    """Check if a client matches campaign trigger criteria.

    Supported trigger fields:
      - min_days_since_visit: last visit was at least N days ago
      - min_visits: client has at least N total visits
      - tags: client has any of these tags
      - source: client came from this source
    """
    if not trigger:
        return True

    min_days = trigger.get("min_days_since_visit")
    if min_days is not None and client.last_visit_at:
        days_since = (datetime.now(UTC) - client.last_visit_at).days
        if days_since < int(min_days):
            return False

    min_visits = trigger.get("min_visits")
    if min_visits is not None and (client.total_visits or 0) < int(min_visits):
        return False

    tags = trigger.get("tags")
    if tags and isinstance(tags, list):
        if not any(t in (client.tags or []) for t in tags):
            return False

    source = trigger.get("source")
    if source and client.source != source:
        return False

    return True


async def execute_campaign(campaign_id: uuid.UUID) -> dict:
    """Run a single campaign: find targets, send messages.

    Called by the Celery beat task. Returns stats dict.
    """
    from app.db.session import AsyncSessionFactory

    async with AsyncSessionFactory() as session:
        campaign = await session.scalar(
            select(Campaign).where(Campaign.id == campaign_id, Campaign.status == "running")
        )
        if not campaign:
            logger.warning("Campaign %s not found or not running, skipping", campaign_id)
            return {"sent": 0, "skipped": 0}

        cfg = await session.scalar(
            select(AIAgentConfig).where(AIAgentConfig.team_id == campaign.team_id)
        )
        template = None
        if campaign.template_id:
            template = await session.scalar(
                select(Template).where(Template.id == campaign.template_id)
            )

        query = select(Client).where(
            Client.team_id == campaign.team_id,
            Client.deleted_at.is_(None),
        )
        clients = (await session.scalars(query)).all()

        channels = campaign.channels or ["whatsapp"]
        sent = 0
        skipped = 0

        for client in clients:
            if not _match_trigger(client, campaign.trigger or {}):
                skipped += 1
                continue

            # Don't re-contact if already reached in this campaign
            existing = await session.scalar(
                select(OutreachAttempt).where(
                    OutreachAttempt.team_id == campaign.team_id,
                    OutreachAttempt.client_id == client.id,
                    OutreachAttempt.reason["campaign_id"].as_string() == str(campaign.id),
                )
            )
            if existing:
                skipped += 1
                continue

            channel = channels[0] if channels else "whatsapp"
            if channel == "telegram" and not client.telegram_chat_id:
                channel = "whatsapp"

            # Render message
            message_text = ""
            if template:
                message_text = _render_template(template.content, client)
            elif cfg and settings.openai_api_key:
                try:
                    client_sdk = AsyncOpenAI(api_key=settings.openai_api_key)
                    resp = await client_sdk.chat.completions.create(
                        model=settings.openai_model,
                        max_tokens=300,
                        messages=[
                            {
                                "role": "system",
                                "text": f"Ты — ассистент автосервиса. Стиль: {cfg.tone}. "
                                        f"Напиши короткое персонализированное сообщение для клиента {client.full_name}.",
                            },
                            {
                                "role": "user",
                                "content": campaign.description
                                or f"Отправь сообщение клиенту {client.full_name} по кампании «{campaign.name}»",
                            },
                        ],
                    )
                    message_text = resp.choices[0].message.content or ""
                except Exception:
                    logger.exception("Campaign LLM call failed for client %s", client.id)

            if not message_text:
                message_text = f"Здравствуйте, {client.full_name}! {campaign.description or 'Мы ждём вас в нашем автосервисе.'}"

            # Find or create conversation
            conv = await session.scalar(
                select(Conversation).where(
                    Conversation.client_id == client.id,
                    Conversation.team_id == campaign.team_id,
                    Conversation.channel == channel,
                    Conversation.status == "active",
                )
            )
            if conv is None:
                conv = Conversation(
                    team_id=campaign.team_id,
                    client_id=client.id,
                    channel=channel,
                    status="active",
                )
                session.add(conv)
                await session.flush()

            now = datetime.now(UTC)
            msg = Message(
                conversation_id=conv.id,
                direction="outbound",
                text=message_text,
                status="sent",
                sent_by="ai",
                sent_at=now,
            )
            session.add(msg)

            attempt = OutreachAttempt(
                team_id=campaign.team_id,
                client_id=client.id,
                conversation_id=conv.id,
                status="sent",
                reason={"campaign_id": str(campaign.id), "campaign_name": campaign.name},
                message_text=message_text,
                sent_at=now,
            )
            session.add(attempt)

            conv.last_message_at = now
            sent += 1

            try:
                from app.services.channel_dispatcher import dispatch
                await dispatch(client.phone, client.telegram_chat_id, channel, message_text)
            except Exception:
                logger.exception("Failed to dispatch campaign message for client %s", client.id)

        # Update campaign stats
        stats = campaign.stats or {}
        stats["sent"] = stats.get("sent", 0) + sent
        stats["skipped"] = stats.get("skipped", 0) + skipped
        campaign.stats = stats

        # One_time campaigns auto-complete
        if campaign.type == "one_time":
            campaign.status = "completed"

        await session.commit()

        logger.info("Campaign %s executed: sent=%d, skipped=%d", campaign_id, sent, skipped)
        return {"sent": sent, "skipped": skipped}