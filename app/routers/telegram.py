import httpx
from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from ..config import settings
from ..db import get_session
from ..models import Message
from ..services.ai import async_chat


router = APIRouter(prefix="/tg", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(req: Request, session: AsyncSession = Depends(get_session)):
    """
    Универсальный вебхук Telegram.
    На вход приходит update. Для MVP: текстовые сообщения -> AI ответ -> сохранение в БД.
    """
    update = await req.json()
    msg = update.get("message") or update.get("edited_message")
    if not msg or "text" not in msg:
        return {"ok": True}

    chat_id = str(msg["chat"]["id"])
    text = msg["text"].strip()

    # сохраняем вход
    m_in = Message(bot_id=1, user_id=chat_id, role="user", text=text)
    session.add(m_in)
    await session.commit()

    # получаем ответ ИИ
    answer = await async_chat([{"role": "user", "content": text}])

    # сохраняем выход
    m_out = Message(bot_id=1, user_id=chat_id, role="assistant", text=answer)
    session.add(m_out)
    await session.commit()

    # отправка ответа обратно в Telegram (простая)
    # здесь — прямой вызов API Telegram (без SDK), чтобы не тянуть лишние пакеты
    if settings.TELEGRAM_BOT_TOKEN:
        send_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(send_url, json={"chat_id": chat_id, "text": answer})

    return {"ok": True}
