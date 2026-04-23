"""Inbound webhooks for external messengers.

Each provider will eventually get its own endpoint with provider-specific
signature verification (Meta's HMAC for WhatsApp Cloud, Telegram's bot
token, etc.). For now we expose a generic endpoint guarded by a shared
secret — enough for bridges and local QA.
"""

from __future__ import annotations

import secrets
from typing import Literal

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import SessionDep
from app.core.limiter import limiter
from app.schemas.conversation import MessagePublicOut
from app.services import inbound_service

router = APIRouter()


class WhatsAppInboundPayload(BaseModel):
    team_slug: str = Field(min_length=1)
    phone: str = Field(min_length=3, max_length=32)
    text: str | None = Field(default=None, max_length=4000)
    media_url: str | None = Field(default=None, max_length=500)
    client_name: str | None = Field(default=None, max_length=255)
    external_id: str | None = Field(default=None, max_length=255)
    channel: Literal["whatsapp", "telegram", "sms"] = "whatsapp"


def _check_secret(provided: str | None) -> None:
    expected = settings.inbound_webhook_secret
    if not expected:
        # Fail closed: no secret configured means webhook is disabled.
        raise HTTPException(status_code=503, detail="Webhook not configured")
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


@router.post("/whatsapp", response_model=MessagePublicOut, status_code=201)
@limiter.limit("120/minute")
async def whatsapp_inbound(
    request: Request,  # noqa: ARG001 — required by slowapi key_func
    payload: WhatsAppInboundPayload,
    session: SessionDep,
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
):
    _check_secret(x_webhook_secret)
    msg = await inbound_service.record_inbound_message(
        team_slug=payload.team_slug,
        channel=payload.channel,
        phone=payload.phone,
        text=payload.text,
        media_url=payload.media_url,
        client_name=payload.client_name,
        external_id=payload.external_id,
        session=session,
    )
    return msg
