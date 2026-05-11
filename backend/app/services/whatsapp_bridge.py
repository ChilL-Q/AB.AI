"""WhatsApp bridge via Twilio.

Twilio supports WhatsApp through the same Messages API — just prefix
the phone number with "whatsapp:". For inbound, Twilio sends webhooks
in its own format (not Cloud API), so we parse differently.

Sandbox mode: before a number is verified in production, the recipient
must send "join <code>" to the Twilio sandbox number via WhatsApp.

Configuration: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
(uses the same credentials as SMS).
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.twilio.com/2010-04-01"


def _is_configured() -> bool:
    return bool(settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_phone_number)


def _whatsapp_from() -> str:
    return f"whatsapp:{settings.twilio_phone_number}"


def _whatsapp_to(phone: str) -> str:
    if phone.startswith("whatsapp:"):
        return phone
    return f"whatsapp:{phone}"


async def send_message(phone: str, text: str) -> dict | None:
    """Send a WhatsApp message via Twilio.

    Returns the Twilio API response dict on success, None on failure.
    """
    if not _is_configured():
        logger.warning("Twilio/WhatsApp not configured — skipping outbound to %s", phone)
        return None

    url = f"{BASE_URL}/Accounts/{settings.twilio_account_sid}/Messages.json"
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)
    data = {
        "From": _whatsapp_from(),
        "To": _whatsapp_to(phone),
        "Body": text,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, auth=auth, data=data)
            resp.raise_for_status()
            result = resp.json()
            logger.info("WhatsApp message sent to %s via Twilio: %s", phone, result.get("sid", ""))
            return result
        except httpx.HTTPStatusError as exc:
            logger.error("Twilio WhatsApp error: %s %s", exc.response.status_code, exc.response.text)
            return None
        except Exception:
            logger.exception("Twilio WhatsApp send failed for %s", phone)
            return None


async def send_template(phone: str, template_name: str, language: str = "ru", components: list | None = None) -> dict | None:
    """Send a WhatsApp template via Twilio.

    Twilio uses Content SIDs for templates. For now, we send as a
    regular text message — templates require pre-approved content in Twilio.
    """
    logger.warning("Twilio WhatsApp templates require Content SID — sending as text instead")
    return await send_message(phone, template_name)


def verify_webhook(mode: str, token: str) -> bool:
    """Twilio doesn't use a GET challenge like Meta.

    This stub always returns False — Twilio webhook verification
    is done via X-Twilio-Signature header instead.
    """
    return False


def parse_inbound(form_data: dict) -> list[dict] | None:
    """Parse a Twilio WhatsApp inbound webhook (application/x-www-form-urlencoded).

    Returns a list of dicts: {phone, text, external_id, client_name}
    or None if no message.
    """
    phone = form_data.get("From", "")
    if phone.startswith("whatsapp:"):
        phone = phone[len("whatsapp:"):]

    text = form_data.get("Body", "")
    num_media = int(form_data.get("NumMedia", "0") or "0")

    if not phone and not text:
        return None

    result = {
        "phone": phone,
        "text": text or None,
        "external_id": form_data.get("MessageSid"),
        "client_name": None,
    }

    if num_media > 0:
        media_url = form_data.get("MediaUrl0")
        if media_url:
            result["media_url"] = media_url
            if not text:
                result["text"] = "[медиа]"

    return [result]