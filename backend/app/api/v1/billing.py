"""Billing / subscription endpoints.

Stub status: plan listing + current subscription + checkout session creation
work. Stripe webhook handler is wired up — needs real keys to process events.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from app.core.deps import CurrentUserDep, SessionDep
from app.core.exceptions import ForbiddenError
from app.services import billing_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _team_id(current_user) -> str:
    if current_user.team_id is None:
        raise ForbiddenError("User has no team")
    return current_user.team_id


class CheckoutRequest(BaseModel):
    plan: str


@router.get("/plans")
async def list_plans():
    return billing_service.PLANS


@router.get("/subscription")
async def get_subscription(current_user: CurrentUserDep, session: SessionDep):
    sub = await billing_service.get_or_create_subscription(
        _team_id(current_user), session
    )
    return {
        "plan": sub.plan,
        "status": sub.status,
        "trial_ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "payment_provider": sub.payment_provider,
    }


@router.post("/checkout")
async def create_checkout(
    data: CheckoutRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    result = await billing_service.create_checkout_session(
        _team_id(current_user), data.plan, session
    )
    return result


@router.post("/cancel")
async def cancel_subscription(current_user: CurrentUserDep, session: SessionDep):
    sub = await billing_service.cancel_subscription(_team_id(current_user), session)
    return {"status": sub.status, "cancel_at_period_end": sub.cancel_at_period_end}


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    logger.info("Stripe webhook received (%d bytes)", len(body))
    try:
        payload = await request.json()
        event_type = payload.get("type", "")
        data = payload.get("data", {}).get("object", {})
        await billing_service.handle_stripe_webhook(event_type, data)
    except Exception:
        logger.exception("Failed to process Stripe webhook")
    return {"status": "ok"}