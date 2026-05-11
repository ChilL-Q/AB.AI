"""Billing service — YooKassa + Kaspi integration for Kazakhstan.

Architecture: hybrid payments
  - YooKassa: recurring auto-payments (tokenized card), also one-time links
  - Kaspi Pay: one-time payment links (no recurring)
  - Halyk Pay (reserved): one-time payment links

Current state: all provider calls are stubs returning placeholders when
keys are not configured. Real integration pending merchant account setup.
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
        "yookassa_price_id": "pro_monthly",
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
        "yookassa_price_id": "business_monthly",
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
    payment_method: str = "yookassa",
    session: AsyncSession | None = None,
) -> dict:
    """Create a payment checkout session.

    payment_method: "yookassa" (recurring), "kaspi" (one-time link)
    """
    if plan not in PLANS:
        raise ValueError(f"Unknown plan: {plan}")

    plan_info = PLANS[plan]
    if plan_info["price_monthly"] == 0:
        if session:
            sub = await get_or_create_subscription(team_id, session)
            sub.plan = plan
            sub.status = "active"
            await session.flush()
        return {"url": None, "message": "Free plan activated"}

    if payment_method == "yookassa":
        return await _yookassa_checkout(team_id, plan, plan_info)
    elif payment_method == "kaspi":
        return await _kaspi_checkout(team_id, plan, plan_info)
    else:
        raise ValueError(f"Unknown payment method: {payment_method}")


async def _yookassa_checkout(team_id: uuid.UUID, plan: str, plan_info: dict) -> dict:
    """YooKassa checkout — supports recurring auto-payments."""
    if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
        logger.warning("YooKassa not configured — returning stub checkout URL")
        return {
            "url": f"https://yookassa.stub/checkout/{plan}?team={team_id}",
            "message": "YooKassa not configured — stub URL",
            "provider": "yookassa",
        }

    import httpx

    url = "https://api.yookassa.ru/v3/payments"
    idempotence_key = str(uuid.uuid4())
    auth = (settings.yookassa_shop_id, settings.yookassa_secret_key)
    payload = {
        "amount": {
            "value": str(plan_info["price_monthly"]),
            "currency": "KZT",
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"{settings.app_url}/settings?billing=success",
        },
        "capture": True,
        "description": f"AB-AI.kz {plan_info['name']} тариф",
        "metadata": {
            "team_id": str(team_id),
            "plan": plan,
        },
        "save_payment_method": True,
        "idempotence_key": idempotence_key,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, auth=auth, json=payload)
            resp.raise_for_status()
            data = resp.json()
            confirmation_url = data.get("confirmation", {}).get("confirmation_url", "")
            return {"url": confirmation_url, "payment_id": data.get("id"), "provider": "yookassa"}
        except httpx.HTTPStatusError as exc:
            logger.error("YooKassa API error: %s %s", exc.response.status_code, exc.response.text)
            return {"url": None, "message": "YooKassa error"}
        except Exception:
            logger.exception("YooKassa checkout failed")
            return {"url": None, "message": "YooKassa error"}


async def _kaspi_checkout(team_id: uuid.UUID, plan: str, plan_info: dict) -> dict:
    """Kaspi Pay — one-time payment link (no recurring)."""
    if not settings.kaspi_merchant_id or not settings.kaspi_api_key:
        logger.warning("Kaspi not configured — returning stub checkout URL")
        return {
            "url": f"https://kaspi.stub/checkout/{plan}?team={team_id}",
            "message": "Kaspi not configured — stub URL",
            "provider": "kaspi",
        }

    # TODO: implement Kaspi Pay API when merchant account is ready
    logger.warning("Kaspi Pay API not yet implemented — returning stub")
    return {
        "url": f"https://kaspi.stub/checkout/{plan}?team={team_id}",
        "message": "Kaspi Pay integration pending merchant setup",
        "provider": "kaspi",
    }


async def handle_yookassa_webhook(event_type: str, data: dict) -> None:
    """Handle YooKassa webhook events."""
    logger.info("YooKassa webhook: %s", event_type)

    from app.db.session import AsyncSessionFactory
    async with AsyncSessionFactory() as session:
        if event_type == "payment.succeeded":
            metadata = data.get("metadata", {})
            team_id_str = metadata.get("team_id")
            plan = metadata.get("plan", "start")
            payment_method_id = data.get("payment_method", {}).get("id")
            payment_id = data.get("id")

            if team_id_str:
                team_id = uuid.UUID(team_id_str)
                sub = await get_subscription(team_id, session)
                if sub:
                    sub.plan = plan
                    sub.status = "active"
                    sub.external_id = payment_id
                    sub.payment_provider = "yookassa"
                    sub.current_period_start = datetime.now(UTC)
                    sub.current_period_end = datetime.now(UTC) + timedelta(days=30)
                    if payment_method_id:
                        sub.payment_method_saved = True  # type: ignore[attr-defined]
                    await session.commit()

        elif event_type == "payment.canceled":
            external_id = data.get("id")
            if external_id:
                sub = await session.scalar(
                    select(Subscription).where(Subscription.external_id == external_id)
                )
                if sub:
                    sub.status = "past_due"
                    await session.commit()

        elif event_type == "recurring.succeeded":
            metadata = data.get("metadata", {})
            team_id_str = metadata.get("team_id")
            if team_id_str:
                team_id = uuid.UUID(team_id_str)
                sub = await get_subscription(team_id, session)
                if sub:
                    sub.status = "active"
                    sub.current_period_start = datetime.now(UTC)
                    sub.current_period_end = datetime.now(UTC) + timedelta(days=30)
                    await session.commit()

        elif event_type == "recurring.canceled":
            metadata = data.get("metadata", {})
            team_id_str = metadata.get("team_id")
            if team_id_str:
                team_id = uuid.UUID(team_id_str)
                sub = await get_subscription(team_id, session)
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