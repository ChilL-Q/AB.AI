"""AI-agent service: config CRUD + reply generation.

The agent is team-scoped: each team has exactly one row in
`ai_agent_configs` (uniq index on team_id). We lazy-create a default on
first read so the frontend never has to special-case 404 during onboarding.

`generate_reply` pulls the last N messages of a conversation plus the
client's card and the team's config, assembles a Russian-first system
prompt, and delegates to OpenAI's Chat Completions API. Failures are
caught and surfaced as a domain error the caller can turn into a toast
or silently skip — we never want AI flakiness to break the write path.

We use `gpt-4o-mini` as the default: ~20x cheaper than Claude Sonnet,
handles Russian well, and fast enough for conversational latency.
Model is configurable via `settings.openai_model` without code changes.
"""

from __future__ import annotations

import logging
import uuid

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.db.models.ai_agent_config import AIAgentConfig
from app.db.models.client import Client
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.schemas.ai_agent import AIAgentConfigUpdate

logger = logging.getLogger(__name__)

# Kept small to bound prompt cost; 20 messages is ~99% of in-session
# context for a support conversation.
REPLY_CONTEXT_MESSAGES = 20
MAX_REPLY_TOKENS = 400


class AIAgentError(Exception):
    """Raised when the upstream LLM call fails or is unconfigured.

    The caller decides whether to log and move on (webhook path) or
    bubble up as a 502 (manual /suggest endpoint).
    """


async def get_config(team_id: uuid.UUID, session: AsyncSession) -> AIAgentConfig:
    """Return the team's config, creating a default row on first access."""
    cfg = await session.scalar(select(AIAgentConfig).where(AIAgentConfig.team_id == team_id))
    if cfg is None:
        cfg = AIAgentConfig(
            team_id=team_id,
            mode="auto",
            is_active=True,
            tone="friendly",
            knowledge_base={},
            forbidden_topics=[],
            escalation_rules={},
        )
        session.add(cfg)
        await session.flush()
        await session.refresh(cfg)
    return cfg


async def update_config(
    team_id: uuid.UUID, patch: AIAgentConfigUpdate, session: AsyncSession
) -> AIAgentConfig:
    cfg = await get_config(team_id, session)
    for field, value in patch.model_dump(exclude_none=True).items():
        setattr(cfg, field, value)
    await session.flush()
    await session.refresh(cfg)
    return cfg


def _build_system_prompt(cfg: AIAgentConfig, client: Client | None) -> str:
    """Compose a Russian-first system prompt that encodes the team's voice
    and hard rules. Kept compact to save tokens; free-form operator input
    (personality/knowledge base) goes last so it can override defaults."""
    parts: list[str] = [
        "Ты — ассистент автосервиса, общаешься с клиентом от имени команды. "
        "Отвечай коротко, по делу, на русском. Если не знаешь ответа — скажи, "
        "что уточнишь у коллег. Никогда не выдумывай цены, сроки и гарантии.",
        f"Стиль общения: {cfg.tone}.",
    ]
    if cfg.personality:
        parts.append(f"Характер: {cfg.personality}")
    if cfg.forbidden_topics:
        topics = ", ".join(cfg.forbidden_topics)
        parts.append(f"Запрещённые темы (не обсуждай, вежливо отклони): {topics}.")
    if cfg.knowledge_base:
        # knowledge_base is a free-form JSON object — render as key: value lines.
        kb_lines = [f"- {k}: {v}" for k, v in cfg.knowledge_base.items()]
        parts.append("База знаний:\n" + "\n".join(kb_lines))
    if client is not None:
        card = [f"Имя: {client.full_name}", f"Телефон: {client.phone}"]
        if client.total_visits:
            card.append(f"Визитов: {client.total_visits}")
        if client.tags:
            card.append(f"Теги: {', '.join(client.tags)}")
        parts.append("Карточка клиента:\n" + "\n".join(card))
    return "\n\n".join(parts)


def _render_history(messages: list[Message]) -> list[dict]:
    """Map DB messages to OpenAI's `messages=[{role, content}]` format.

    Inbound (from customer) → `user`; outbound (operator or AI) → `assistant`.
    Messages without text (pure media) are represented as a short stub so
    the model still sees the turn-taking structure.
    """
    out: list[dict] = []
    for m in messages:
        role = "user" if m.direction == "inbound" else "assistant"
        content = m.text or "[вложение без текста]"
        out.append({"role": role, "content": content})
    return out


async def generate_reply(
    *, conversation_id: uuid.UUID, team_id: uuid.UUID, session: AsyncSession
) -> str:
    """Produce a single reply for the given conversation.

    Raises AIAgentError on any upstream failure (missing key, API error,
    blocked content). Never mutates the DB.
    """
    if not settings.openai_api_key:
        raise AIAgentError("OPENAI_API_KEY is not configured")

    conv = await session.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.team_id == team_id
        )
    )
    if conv is None:
        raise NotFoundError("Conversation not found")

    cfg = await get_config(team_id, session)
    client = await session.scalar(select(Client).where(Client.id == conv.client_id))

    rows = (
        await session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(REPLY_CONTEXT_MESSAGES)
        )
    ).all()
    # The query fetches newest-first for the LIMIT to work; flip to chronological.
    history = list(rows)
    history.reverse()

    # Defend against threads that start with an assistant row (shouldn't
    # normally happen, but keep the model anchored on a user turn).
    while history and history[0].direction != "inbound":
        history.pop(0)
    if not history:
        raise AIAgentError("No inbound message to reply to")

    system_prompt = _build_system_prompt(cfg, client)
    # OpenAI takes system as the first message, not a separate param.
    conv_messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        *_render_history(history),
    ]

    client_sdk = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        resp = await client_sdk.chat.completions.create(
            model=settings.openai_model,
            max_tokens=MAX_REPLY_TOKENS,
            messages=conv_messages,  # type: ignore[arg-type]
        )
    except Exception as exc:  # noqa: BLE001 — wrap-and-raise a domain error
        logger.exception("OpenAI API call failed (conv=%s)", conversation_id)
        raise AIAgentError(f"LLM call failed: {exc}") from exc

    if not resp.choices:
        raise AIAgentError("LLM returned no choices")
    text = resp.choices[0].message.content
    if not text:
        raise AIAgentError("LLM returned empty content")
    return text.strip()
