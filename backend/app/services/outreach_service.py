"""Proactive AI Outreach service.

The core insight: AI doesn't just answer inbound messages — it decides
*who to write to, when, and what to say* based on visit history.

Flow:
  1. Periodic Celery task calls `run_outreach_cycle(team_id)`.
  2. The engine fetches clients with stale visit history.
  3. It builds a prompt with all client + visit data and asks the LLM
     which clients to contact and what to say.
  4. For each candidate: create OutreachAttempt, find/create conversation,
     send the message.
  5. Cooldown: 24h between attempts per client. After 2 unanswered attempts,
     escalate to the business owner.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.ai_agent_config import AIAgentConfig
from app.db.models.car import Car
from app.db.models.client import Client
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.outreach_attempt import OutreachAttempt
from app.db.models.visit import Visit
from app.schemas.outreach import OutreachActionOut

logger = logging.getLogger(__name__)

COOLDOWN_HOURS = 24
MAX_UNANSWERED_BEFORE_ESCALATE = 2
OUTREACH_MAX_TOKENS = 600


def _build_outreach_prompt(cfg: AIAgentConfig, clients_data: list[dict]) -> str:
    parts = [
        "Ты — проактивный AI-ассистент автосервиса. Твоя задача — решить, "
        "каким клиентам стоит написать прямо сейчас, чтобы они вернулись, "
        "и придумать персонализированное сообщение для каждого.\n\n"
        "Правила:\n"
        "- Пиши только тем, у кого давно не было визита или подходит время "
        "повторной услуги (замена масла, ТО и т.д.).\n"
        "- Сообщения должны быть короткие, дружелюбные, на русском.\n"
        "- Предлагай конкретное действие: записаться на время, приехать на ТО.\n"
        f"- Стиль: {cfg.tone}.",
    ]
    if cfg.personality:
        parts.append(f"Характер: {cfg.personality}")
    if cfg.knowledge_base:
        kb_lines = [f"- {k}: {v}" for k, v in cfg.knowledge_base.items()]
        parts.append("База знаний:\n" + "\n".join(kb_lines))

    parts.append("\nКандидаты для обращения:\n")
    for cd in clients_data:
        line = (
            f"- Клиент: {cd['name']} (ID: {cd['id']}). "
            f"Последний визит: {cd['last_visit']}. "
            f"Всего визитов: {cd['total_visits']}. "
            f"История услуг: {cd['services_summary']}. "
            f"Авто: {cd['cars_summary']}."
        )
        if cd.get("due_services"):
            line += f" СРОЧНО: {cd['due_services']}"
        parts.append(line)

    parts.append(
        "\nОтветь в формате JSON-массива. Каждый элемент: "
        '{"client_id": "<id>", "reason": "<почему пишем>", '
        '"message": "<текст сообщения>"}. '
        "Если никому писать не нужно — верни пустой массив []."
    )
    return "\n\n".join(parts)


async def _get_outreach_candidates(team_id: uuid.UUID, session: AsyncSession) -> list[dict]:
    cooldown_cutoff = datetime.now(UTC) - timedelta(hours=COOLDOWN_HOURS)

    recently_contacted = select(OutreachAttempt.client_id).where(
        OutreachAttempt.team_id == team_id,
        OutreachAttempt.sent_at >= cooldown_cutoff,
    )

    rows = await session.execute(
        select(Client).where(
            Client.team_id == team_id,
            Client.deleted_at.is_(None),
            Client.do_not_contact.is_(False),
            Client.id.notin_(recently_contacted),
        )
    )
    clients = rows.scalars().all()

    from app.services.service_reminder import get_due_services
    due_services = await get_due_services(team_id, session)
    due_by_client: dict[str, list[str]] = {}
    for ds in due_services:
        cid = ds["client_id"]
        due_by_client.setdefault(cid, []).append(f"{ds['service_name']}: {ds['reason']}")

    candidates = []
    for c in clients:
        unanswered_count = await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt)
                .where(
                    OutreachAttempt.client_id == c.id,
                    OutreachAttempt.team_id == team_id,
                    OutreachAttempt.status.in_(["sent", "pending"]),
                    OutreachAttempt.replied_at.is_(None),
                )
                .subquery()
            )
        )
        if (unanswered_count or 0) >= MAX_UNANSWERED_BEFORE_ESCALATE:
            continue

        last_visit = c.last_visit_at.isoformat() if c.last_visit_at else "никогда"

        services_raw = await session.scalar(
            select(func.json_agg(Visit.services)).where(
                Visit.client_id == c.id, Visit.team_id == team_id
            )
        )
        all_services: list[str] = []
        if services_raw:
            for svc_list in services_raw:
                if isinstance(svc_list, list):
                    for svc in svc_list:
                        if isinstance(svc, dict) and svc.get("name"):
                            all_services.append(svc["name"])

        car_result = await session.execute(select(Car).where(Car.client_id == c.id))
        car_list = car_result.scalars().all()
        cars_summary = (
            ", ".join(f"{cr.brand} {cr.model} ({cr.year or ''})" for cr in car_list) or "нет данных"
        )

        candidate = {
            "id": str(c.id),
            "name": c.full_name,
            "last_visit": last_visit,
            "total_visits": c.total_visits,
            "services_summary": ", ".join(all_services[:10]) or "нет данных",
            "cars_summary": cars_summary,
        }
        if str(c.id) in due_by_client:
            candidate["due_services"] = "; ".join(due_by_client[str(c.id)])

        candidates.append(candidate)

    return candidates


async def run_outreach_cycle(team_id: uuid.UUID, session: AsyncSession) -> list[OutreachActionOut]:
    cfg = await session.scalar(select(AIAgentConfig).where(AIAgentConfig.team_id == team_id))
    if not cfg or not cfg.is_active:
        return []

    candidates = await _get_outreach_candidates(team_id, session)
    if not candidates:
        return []

    if not settings.openai_api_key:
        logger.warning("Outreach skipped: OPENAI_API_KEY not configured (team=%s)", team_id)
        return []

    prompt = _build_outreach_prompt(cfg, candidates)
    client_sdk = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        resp = await client_sdk.chat.completions.create(
            model=settings.openai_model,
            max_tokens=OUTREACH_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
    except Exception:
        logger.exception("Outreach LLM call failed (team=%s)", team_id)
        return []

    if not resp.choices:
        return []

    content = resp.choices[0].message.content or ""
    try:
        parsed = json.loads(content)
        items = parsed if isinstance(parsed, list) else parsed.get("clients", [])
    except json.JSONDecodeError:
        logger.warning("Outreach LLM returned invalid JSON (team=%s)", team_id)
        return []

    results: list[OutreachActionOut] = []
    for item in items[:20]:
        client_id_str = item.get("client_id", "")
        try:
            client_id = uuid.UUID(client_id_str)
        except ValueError:
            continue

        client = await session.scalar(
            select(Client).where(Client.id == client_id, Client.team_id == team_id)
        )
        if not client or client.do_not_contact:
            continue

        channel = "telegram" if client.telegram_chat_id else "whatsapp"

        conv = await session.scalar(
            select(Conversation).where(
                Conversation.client_id == client_id,
                Conversation.team_id == team_id,
                Conversation.status == "active",
                Conversation.channel == channel,
            )
        )
        if conv is None:
            conv = Conversation(
                team_id=team_id,
                client_id=client_id,
                channel=channel,
                status="active",
            )
            session.add(conv)
            await session.flush()

        is_auto = cfg.mode == "auto"
        attempt_status = "sent" if is_auto else "pending"
        sent_time = datetime.now(UTC) if is_auto else None

        attempt = OutreachAttempt(
            team_id=team_id,
            client_id=client_id,
            conversation_id=conv.id,
            status=attempt_status,
            reason={"text": item.get("reason", "")},
            message_text=item.get("message", ""),
            sent_at=sent_time,
        )
        session.add(attempt)
        await session.flush()

        if is_auto:
            now = datetime.now(UTC)
            msg = Message(
                conversation_id=conv.id,
                direction="outbound",
                text=item.get("message", ""),
                status="sent",
                sent_by="ai",
                sent_at=now,
            )
            session.add(msg)
            conv.last_message_at = now
            await session.flush()

            try:
                from app.services.channel_dispatcher import dispatch
                await dispatch(client.phone, client.telegram_chat_id, channel, item.get("message", ""))
            except Exception:
                logger.exception("Failed to dispatch outreach to channel for client %s", client.id)

        results.append(
            OutreachActionOut(
                id=attempt.id,
                client_id=client_id,
                client_name=client.full_name,
                status=attempt_status,
                reason=attempt.reason,
                message_text=attempt.message_text,
                sent_at=sent_time,
                resulted_in_visit=False,
                resulted_in_revenue=Decimal("0"),
                created_at=attempt.created_at,
            )
        )

    await session.commit()
    return results


async def get_outreach_actions(
    team_id: uuid.UUID, session: AsyncSession, limit: int = 50
) -> list[OutreachActionOut]:
    rows = await session.execute(
        select(OutreachAttempt)
        .where(OutreachAttempt.team_id == team_id)
        .order_by(OutreachAttempt.created_at.desc())
        .limit(limit)
    )
    attempts = rows.scalars().all()

    result: list[OutreachActionOut] = []
    for a in attempts:
        client = await session.scalar(select(Client).where(Client.id == a.client_id))
        result.append(
            OutreachActionOut(
                id=a.id,
                client_id=a.client_id,
                client_name=client.full_name if client else "Unknown",
                status=a.status,
                reason=a.reason,
                message_text=a.message_text,
                sent_at=a.sent_at,
                replied_at=a.replied_at,
                resulted_in_visit=a.resulted_in_visit,
                resulted_in_revenue=a.resulted_in_revenue,
                created_at=a.created_at,
            )
        )
    return result


async def get_outreach_metrics(team_id: uuid.UUID, session: AsyncSession) -> dict:
    total = (
        await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt).where(OutreachAttempt.team_id == team_id).subquery()
            )
        )
        or 0
    )

    replied = (
        await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt)
                .where(OutreachAttempt.team_id == team_id, OutreachAttempt.replied_at.isnot(None))
                .subquery()
            )
        )
        or 0
    )

    resulted_visit = (
        await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt)
                .where(
                    OutreachAttempt.team_id == team_id, OutreachAttempt.resulted_in_visit.is_(True)
                )
                .subquery()
            )
        )
        or 0
    )

    total_revenue = await session.scalar(
        select(func.coalesce(func.sum(OutreachAttempt.resulted_in_revenue), 0)).where(
            OutreachAttempt.team_id == team_id
        )
    ) or Decimal("0")

    escalated = (
        await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt)
                .where(OutreachAttempt.team_id == team_id, OutreachAttempt.status == "escalated")
                .subquery()
            )
        )
        or 0
    )

    return {
        "total_outreach": total,
        "replied": replied,
        "reply_rate": round(replied / total, 3) if total else 0,
        "resulted_in_visit": resulted_visit,
        "retention_rate": round(resulted_visit / total, 3) if total else 0,
        "total_revenue": float(total_revenue),
        "escalated": escalated,
    }


async def mark_outreach_replied(attempt_id: uuid.UUID, session: AsyncSession) -> None:
    attempt = await session.scalar(select(OutreachAttempt).where(OutreachAttempt.id == attempt_id))
    if attempt:
        attempt.status = "replied"
        attempt.replied_at = datetime.now(UTC)
        await session.flush()


async def check_and_escalate(team_id: uuid.UUID, session: AsyncSession) -> list[uuid.UUID]:
    """Find unanswered outreach attempts past the escalation threshold.

    For each, mark as escalated and return client IDs so the caller can
    notify the business owner.
    """
    cutoff = datetime.now(UTC) - timedelta(hours=COOLDOWN_HOURS * 2)

    rows = await session.execute(
        select(OutreachAttempt).where(
            OutreachAttempt.team_id == team_id,
            OutreachAttempt.status == "sent",
            OutreachAttempt.replied_at.is_(None),
            OutreachAttempt.sent_at <= cutoff,
        )
    )
    to_escalate = rows.scalars().all()

    escalated_client_ids: list[uuid.UUID] = []
    for a in to_escalate:
        a.status = "escalated"
        escalated_client_ids.append(a.client_id)

    if to_escalate:
        await session.flush()

    return escalated_client_ids


async def trigger_outreach(
    team_id: uuid.UUID,
    client_id: uuid.UUID,
    session: AsyncSession,
    *,
    custom_message: str | None = None,
    custom_reason: str | None = None,
) -> OutreachActionOut:
    """Manually trigger outreach to a specific client.

    If custom_message is provided, use it directly. Otherwise ask the LLM
    to generate a personalized message based on the client's history.
    """
    cfg = await session.scalar(select(AIAgentConfig).where(AIAgentConfig.team_id == team_id))
    if not cfg:
        from app.core.exceptions import BadRequestError
        raise BadRequestError("AI agent config not found — save agent settings first")

    client = await session.scalar(
        select(Client).where(Client.id == client_id, Client.team_id == team_id, Client.deleted_at.is_(None))
    )
    if not client:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Client not found")

    message_text = custom_message
    reason_text = custom_reason or "Manual outreach"

    if not message_text and settings.openai_api_key:
        car_result = await session.execute(select(Car).where(Car.client_id == client_id))
        car_list = car_result.scalars().all()
        cars_summary = (
            ", ".join(f"{cr.brand} {cr.model} ({cr.year or ''})" for cr in car_list) or "нет данных"
        )

        services_raw = await session.scalar(
            select(func.json_agg(Visit.services)).where(
                Visit.client_id == client_id, Visit.team_id == team_id
            )
        )
        all_services: list[str] = []
        if services_raw:
            for svc_list in services_raw:
                if isinstance(svc_list, list):
                    for svc in svc_list:
                        if isinstance(svc, dict) and svc.get("name"):
                            all_services.append(svc["name"])

        client_data = {
            "id": str(client.id),
            "name": client.full_name,
            "last_visit": client.last_visit_at.isoformat() if client.last_visit_at else "никогда",
            "total_visits": client.total_visits,
            "services_summary": ", ".join(all_services[:10]) or "нет данных",
            "cars_summary": cars_summary,
        }

        prompt = _build_outreach_prompt(cfg, [client_data])
        client_sdk = AsyncOpenAI(api_key=settings.openai_api_key)

        try:
            resp = await client_sdk.chat.completions.create(
                model=settings.openai_model,
                max_tokens=OUTREACH_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or ""
            parsed = json.loads(content)
            items = parsed if isinstance(parsed, list) else parsed.get("clients", [])
            if items:
                message_text = items[0].get("message", "")
                if not custom_reason:
                    reason_text = items[0].get("reason", reason_text)
        except Exception:
            logger.exception("Manual outreach LLM call failed (team=%s, client=%s)", team_id, client_id)

    if not message_text:
        message_text = f"Здравствуйте, {client.full_name}! Мы давно вас не видели. Записаться на сервис?"

    channel = "telegram" if client.telegram_chat_id else "whatsapp"

    conv = await session.scalar(
        select(Conversation).where(
            Conversation.client_id == client_id,
            Conversation.team_id == team_id,
            Conversation.status == "active",
            Conversation.channel == channel,
        )
    )
    if conv is None:
        conv = Conversation(
            team_id=team_id,
            client_id=client_id,
            channel=channel,
            status="active",
        )
        session.add(conv)
        await session.flush()

    attempt = OutreachAttempt(
        team_id=team_id,
        client_id=client_id,
        conversation_id=conv.id,
        status="pending",
        reason={"text": reason_text},
        message_text=message_text,
    )
    session.add(attempt)
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
    conv.last_message_at = now
    attempt.status = "sent"
    attempt.sent_at = now
    await session.flush()
    await session.commit()

    try:
        from app.services.channel_dispatcher import dispatch
        await dispatch(client.phone, client.telegram_chat_id, channel, message_text)
    except Exception:
        logger.exception("Failed to dispatch manual outreach to channel for client %s", client_id)

    return OutreachActionOut(
        id=attempt.id,
        client_id=client_id,
        client_name=client.full_name,
        status="sent",
        reason=attempt.reason,
        message_text=attempt.message_text,
        sent_at=now,
        resulted_in_visit=False,
        resulted_in_revenue=Decimal("0"),
        created_at=attempt.created_at,
    )


async def approve_outreach(
    attempt_id: uuid.UUID,
    session: AsyncSession,
    *,
    edited_message: str | None = None,
) -> OutreachActionOut:
    """Approve a pending outreach attempt and send it."""
    attempt = await session.scalar(
        select(OutreachAttempt).where(OutreachAttempt.id == attempt_id)
    )
    if not attempt:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Outreach attempt not found")
    if attempt.status != "pending":
        from app.core.exceptions import BadRequestError
        raise BadRequestError("Only pending attempts can be approved")

    client = await session.scalar(
        select(Client).where(Client.id == attempt.client_id)
    )
    if not client:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Client not found")

    message_text = edited_message or attempt.message_text or ""
    channel = "telegram" if client.telegram_chat_id else "whatsapp"

    conv = attempt.conversation_id and await session.scalar(
        select(Conversation).where(Conversation.id == attempt.conversation_id)
    )
    if not conv:
        conv = Conversation(
            team_id=attempt.team_id,
            client_id=attempt.client_id,
            channel=channel,
            status="active",
        )
        session.add(conv)
        await session.flush()
        attempt.conversation_id = conv.id

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
    conv.last_message_at = now
    attempt.status = "sent"
    attempt.sent_at = now
    if edited_message:
        attempt.message_text = edited_message
    await session.flush()

    try:
        from app.services.channel_dispatcher import dispatch
        await dispatch(client.phone, client.telegram_chat_id, channel, message_text)
    except Exception:
        logger.exception("Failed to dispatch approved outreach for client %s", client.id)

    return OutreachActionOut(
        id=attempt.id,
        client_id=attempt.client_id,
        client_name=client.full_name,
        status="sent",
        reason=attempt.reason,
        message_text=attempt.message_text,
        sent_at=now,
        resulted_in_visit=False,
        resulted_in_revenue=Decimal("0"),
        created_at=attempt.created_at,
    )


async def reject_outreach(attempt_id: uuid.UUID, session: AsyncSession) -> None:
    """Reject (cancel) a pending outreach attempt."""
    attempt = await session.scalar(
        select(OutreachAttempt).where(OutreachAttempt.id == attempt_id)
    )
    if not attempt:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Outreach attempt not found")
    if attempt.status != "pending":
        from app.core.exceptions import BadRequestError
        raise BadRequestError("Only pending attempts can be rejected")
    attempt.status = "failed"
    await session.flush()
