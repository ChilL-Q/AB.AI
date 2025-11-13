import os
import httpx
from ..config import settings

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are AB.AI — an AI assistant for small businesses. "
    "Be concise, helpful, and ask clarifying questions only when necessary."
)


async def async_chat(messages: list[dict]) -> str:
    """
    Минимальный вызов OpenAI Chat Completions (совместим с gpt-4o-mini и аналогами).
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        # офлайн-заглушка, если ключа нет
        return "👋 (demo) Я — ассистент AB.AI. Подключите OPENAI_API_KEY для реальных ответов."
    payload = {
        "model": settings.AI_MODEL,
        "messages": [{"role":"system","content":SYSTEM_PROMPT}] + messages,
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            OPENAI_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
