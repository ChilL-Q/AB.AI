from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func
from ..models import Message


async def basic_counters(session: AsyncSession) -> dict:
    q1 = await session.execute(select(func.count(Message.id)))
    total_msgs = q1.scalar() or 0

    q2 = await session.execute(select(func.sum(Message.revenue_cents)))
    revenue_cents = q2.scalar() or 0

    q3 = await session.execute(select(func.count(Message.id)).where(Message.role == "user"))
    user_msgs = q3.scalar() or 0

    q4 = await session.execute(select(func.count(Message.id)).where(Message.role == "assistant"))
    ai_msgs = q4.scalar() or 0

    return {
        "messages_total": total_msgs,
        "messages_user": user_msgs,
        "messages_ai": ai_msgs,
        "revenue": round(revenue_cents / 100, 2),
        "roi_stub": "Тут позже считаем ROI = (Доход - Затраты)/Затраты",
    }
