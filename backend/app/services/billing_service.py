"""Billing service — Stripe integration stub.

Current state: returns plan info, creates checkout sessions (requires real
Stripe keys), and handles webhook events. Real Stripe calls are guarded behind
self.stripe_client — when keys are empty, we return stub responses.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.subscription import Subscription
from app.core.config import settings

logger = logging.getLogger(__name__)

PLANS = {
    "start": {
        "name": "Start",
        "price_monthly": 0,
        "price_label": "Бесплатно",
        "clients_limit": 100,
        "ai_messages_monthly": 200,
        "channels": ["telegram"],
        "features": ["Базовый AI-ответчик", "До 100 клиентов", "Telegram"],
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 14990,
        "price_label": "14 990 ₸/мес",
        "clients_limit": 1000,
        "ai_messages_monthly": 2000,
        "channels": ["telegram", "whatsapp", "sms"],
        "features": [
            "AI-агент auto + semi_auto",
            "До 1000 клиентов",
            "Все каналы",
            "Сервисные интервалы",
            "Метрики удержания",
        ],
        "stripe_price_id": "price_pro_monthly",
    },
    "business": {
        "name": "Business",
        "price_monthly": 39990,
        "price_label": "39 990 ₸/мес",
        "clients_limit": None,
        "ai_messages_monthly": None,
        "channels": ["telegram", "whatsapp", "sms"],
        "features": [
            "Безлимитные клиенты",
            "Безлимит AI-сообщений",
            "Все каналы",
            "API-интеграции",
            "Приоритетная поддержка",
        ],
        "stripe_price_id": "price_business_monthly",
    },
}


async def get_subscription(team_id: uuid.UUID, session: AsyncSession) -> Subscription | None:
    return await session.scalar(
        select(Subscription).where(Subscription.team_id == team_id)
    )


async def create_trial_subscription(team_id: uuid.UUID, session: AsyncSession) -> Subscription:
    sub = Subscription(
        team_id=team_id,
        plan="start",
        status="trialing",
        trial_ends_at=datetime.now(UTC) + timedelta(days=14),
        current_period_start=datetime.now(UTC),
        current_period_end=datetime.now(UTC) + timedelta(days=14),
    )
    session.add(sub)
    await session.flush()
    return sub


async def get_or_create_subscription(team_id: uuid.UUID, session: AsyncSession) -> Subscription:
    sub = await get_subscription(team_id, session)
    if sub:
        return sub
    return await create_trial_subscription(team_id, session)


async def create_checkout_session(
    team_id: uuid.UUID,
    plan: str,
    session: AsyncSession,
) -> dict:
    if plan not in PLANS:
        raise ValueError(f"Unknown plan: {plan}")

    plan_info = PLANS[plan]
    if plan_info["price_monthly"] == 0:
        sub = await get_or_create_subscription(team_id, session)
        sub.plan = plan
        sub.status = "active"
        await session.flush()
        return {"url": None, "message": "Free plan activated"}

    if not settings.stripe_secret_key:
        logger.warning("Stripe not configured, returning stub checkout URL")
        return {
            "url": f"https://billing.stub/checkout/{plan}?team={team_id}",
            "message": "Stripe not configured — stub URL",
        }

    import stripe
    stripe.api_key = settings.stripe_secret_key

    checkout = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": plan_info["stripe_price_id"], "quantity": 1}],
        success_url=f"{settings.app_url}/settings?billing=success",
        cancel_url=f"{settings.app_url}/settings?billing=cancel",
        metadata={"team_id": str(team_id), "plan": plan},
    )
    return {"url": checkout.url}


async def handle_stripe_webhook(event_type: str, data: dict) -> None:
    logger.info("Stripe webhook: %s", event_type)

    from app.db.session import AsyncSessionFactory
    async with AsyncSessionFactory() as session:
        if event_type == "checkout.session.completed":
            team_id_str = data.get("metadata", {}).get("team_id")
            plan = data.get("metadata", {}).get("plan", "start")
            external_id = data.get("subscription")
            if team_id_str:
                team_id = uuid.UUID(team_id_str)
                sub = await get_subscription(team_id, session)
                if sub:
                    sub.plan = plan
                    sub.status = "active"
                    sub.external_id = external_id
                    sub.payment_provider = "stripe"
                    sub.current_period_start = datetime.now(UTC)
                    sub.current_period_end = datetime.now(UTC) + timedelta(days=30)
                    await session.commit()

        elif event_type == "customer.subscription.updated":
            external_id = data.get("id")
            status = data.get("status")
            if external_id:
                sub = await session.scalar(
                    select(Subscription).where(Subscription.external_id == external_id)
                )
                if sub:
                    sub.status = status
                    await session.commit()

        elif event_type == "customer.subscription.deleted":
            external_id = data.get("id")
            if external_id:
                sub = await session.scalar(
                    select(Subscription).where(Subscription.external_id == external_id)
                )
                if sub:
                    sub.status = "canceled"
                    sub.cancel_at_period_end = True
                    await session.commit()


async def cancel_subscription(team_id: uuid.UUID, session: AsyncSession) -> Subscription:
    sub = await get_subscription(team_id, session)
    if not sub:
        raise ValueError("No subscription found")
    sub.cancel_at_period_end = True
    await session.flush()
    return sub