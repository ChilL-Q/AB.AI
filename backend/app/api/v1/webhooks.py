"""Inbound webhooks for external messengers.

WhatsApp:  GET  /webhooks/whatsapp  — Meta verification handshake
           POST /webhooks/whatsapp  — Inbound messages from Meta Cloud API
Telegram:  POST /webhooks/telegram  — Inbound updates from Telegram Bot API
Generic:   POST /webhooks/inbound   — Shared-secret endpoint for bridges/local QA
"""

from __future__ import annotations

import logging
import secrets
from typing import Literal

from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.limiter import limiter
from app.schemas.conversation import MessagePublicOut
from app.services import inbound_service, telegram_bridge, whatsapp_bridge

router = APIRouter()
logger = logging.getLogger(__name__)


class GenericInboundPayload(BaseModel):
    team_slug: str = Field(min_length=1)
    phone: str = Field(min_length=3, max_length=32)
    text: str | None = Field(default=None, max_length=4000)
    media_url: str | None = Field(default=None, max_length=500)
    client_name: str | None = Field(default=None, max_length=255)
    external_id: str | None = Field(default=None, max_length=255)
    channel: Literal["whatsapp", "telegram", "sms"] = "whatsapp"


# ─── WhatsApp ──────────────────────────────────────────────

@router.get("/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
):
    """Meta/360dialog webhook verification (GET). Twilio doesn't use this."""
    if whatsapp_bridge.verify_webhook(hub_mode, hub_verify_token):
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp", status_code=200)
async def whatsapp_webhook(request: Request):
    """WhatsApp inbound messages (POST).

    Handles both formats:
    - Meta/360dialog Cloud API: JSON body
    - Twilio: application/x-www-form-urlencoded
    Returns 200 immediately.
    """
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        form_data = dict(form)
        parsed = whatsapp_bridge.parse_inbound(form_data)
    else:
        body = await request.json()
        parsed = whatsapp_bridge.parse_inbound(body)
    if not parsed:
        return {"status": "ok"}

    team_slug = settings.team_slug_default or "default"

    for msg in parsed:
        try:
            await inbound_service.record_inbound_message(
                team_slug=team_slug,
                channel="whatsapp",
                phone=msg["phone"],
                text=msg.get("text"),
                client_name=msg.get("client_name"),
                external_id=msg.get("external_id"),
            )
        except Exception:
            logger.exception("Failed to record WhatsApp inbound from %s", msg.get("phone"))

    return {"status": "ok"}


# ─── Telegram ─────────────────────────────────────────────

@router.post("/telegram", status_code=200)
async def telegram_webhook(request: Request):
    """Telegram Bot API inbound updates (POST). Returns 200 immediately."""
    body = await request.json()
    parsed = telegram_bridge.parse_inbound(body)
    if not parsed:
        return {"status": "ok"}

    team_slug = settings.team_slug_default or "default"

    for msg in parsed:
        try:
            await inbound_service.record_inbound_message(
                team_slug=team_slug,
                channel="telegram",
                phone=msg.get("chat_id", ""),
                text=msg.get("text"),
                client_name=msg.get("client_name"),
                external_id=msg.get("external_id"),
                telegram_chat_id=msg.get("chat_id"),
                telegram_username=msg.get("telegram_user_id"),
            )
        except Exception:
            logger.exception("Failed to record Telegram inbound from %s", msg.get("chat_id"))

    return {"status": "ok"}


# ─── Generic (shared-secret) ──────────────────────────────

class _SecretCheck:
    @staticmethod
    def verify(provided: str | None) -> None:
        expected = settings.inbound_webhook_secret
        if not expected:
            raise HTTPException(status_code=503, detail="Webhook not configured")
        if not provided or not secrets.compare_digest(provided, expected):
            raise HTTPException(status_code=401, detail="Invalid webhook secret")


@router.post("/inbound", response_model=MessagePublicOut, status_code=201)
@limiter.limit("120/minute")
async def generic_inbound(
    request: Request,
    payload: GenericInboundPayload,
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
):
    """Generic inbound endpoint guarded by a shared secret."""
    _SecretCheck.verify(x_webhook_secret)
    msg = await inbound_service.record_inbound_message(
        team_slug=payload.team_slug,
        channel=payload.channel,
        phone=payload.phone,
        text=payload.text,
        media_url=payload.media_url,
        client_name=payload.client_name,
        external_id=payload.external_id,
    )
    return MessagePublicOut.model_validate(msg)