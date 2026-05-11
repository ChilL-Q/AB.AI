"""SMS bridge via Twilio.

Sends outbound SMS messages through the Twilio API.
Configuration: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER.
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.twilio.com/2010-04-01"


async def send_message(to_phone: str, text: str) -> dict | None:
    """Send an SMS to a phone number via Twilio.

    Returns the Twilio API response dict on success, None on failure.
    """
    if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_phone_number:
        logger.warning("Twilio credentials not configured — skipping SMS to %s", to_phone)
        return None

    url = f"{BASE_URL}/Accounts/{settings.twilio_account_sid}/Messages.json"
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)
    data = {
        "From": settings.twilio_phone_number,
        "To": to_phone,
        "Body": text,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, auth=auth, data=data)
            resp.raise_for_status()
            result = resp.json()
            logger.info("SMS sent to %s: %s", to_phone, result.get("sid", ""))
            return result
        except httpx.HTTPStatusError as exc:
            logger.error("Twilio API error: %s %s", exc.response.status_code, exc.response.text)
            return None
        except Exception:
            logger.exception("SMS send failed for %s", to_phone)
            return None