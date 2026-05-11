"""Telegram Bot API bridge.

Sends outbound messages via the Telegram Bot API and parses inbound
webhook payloads. Configuration comes from settings:
  - TELEGRAM_BOT_TOKEN
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.telegram.org"


async def send_message(chat_id: str, text: str, parse_mode: str | None = None) -> dict | None:
    """Send a text message to a Telegram chat.

    Returns the API response dict on success, None on failure.
    """
    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not configured — skipping outbound to chat %s", chat_id)
        return None

    url = f"{BASE_URL}/bot{settings.telegram_bot_token}/sendMessage"
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.info("Telegram message sent to chat %s: ok=%s", chat_id, data.get("ok"))
            return data
        except httpx.HTTPStatusError as exc:
            logger.error("Telegram API error: %s %s", exc.response.status_code, exc.response.text)
            return None
        except Exception:
            logger.exception("Telegram send failed for chat %s", chat_id)
            return None


def parse_inbound(body: dict) -> list[dict] | None:
    """Parse a Telegram webhook payload into our inbound format.

    Returns a list of dicts with keys: chat_id, text, external_id, client_name
    or None if the payload contains no messages.
    """
    messages = []

    # Handle regular messages
    if "message" in body:
        msg = body["message"]
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = msg.get("text")
        external_id = str(msg.get("message_id", ""))
        client_name = msg.get("from", {}).get("first_name") or msg.get("from", {}).get("username")

        messages.append({
            "chat_id": chat_id,
            "text": text,
            "external_id": external_id,
            "client_name": client_name,
            "telegram_user_id": str(msg.get("from", {}).get("id", "")),
        })

    # Handle callback queries (inline button presses)
    elif "callback_query" in body:
        cb = body["callback_query"]
        chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
        text = cb.get("data")
        external_id = str(cb.get("id", ""))
        client_name = cb.get("from", {}).get("first_name")

        messages.append({
            "chat_id": chat_id,
            "text": text,
            "external_id": external_id,
            "client_name": client_name,
            "telegram_user_id": str(cb.get("from", {}).get("id", "")),
        })

    return messages if messages else None