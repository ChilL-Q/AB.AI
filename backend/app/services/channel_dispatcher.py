"""Channel dispatcher — routes outbound messages to the right bridge.

When a message is sent (by AI or human operator), we need to actually
deliver it to WhatsApp, Telegram, or SMS. This module picks the bridge
based on the conversation's channel and the client's contact info.
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.services import sms_bridge, telegram_bridge, whatsapp_bridge

logger = logging.getLogger(__name__)


async def dispatch(phone: str | None, telegram_chat_id: str | None, channel: str, text: str) -> bool:
    """Send an outbound message through the appropriate channel bridge.

    Returns True if the message was sent successfully (or bridge is not configured,
    in which case we log a warning but don't block the write path).
    """
    if channel == "whatsapp" and phone:
        result = await whatsapp_bridge.send_message(phone, text)
        return result is not None

    if channel == "telegram" and telegram_chat_id:
        result = await telegram_bridge.send_message(telegram_chat_id, text)
        return result is not None

    if channel == "sms" and phone:
        result = await sms_bridge.send_message(phone, text)
        return result is not None

    if not telegram_chat_id and phone:
        result = await sms_bridge.send_message(phone, text)
        if result is not None:
            return True
        result = await whatsapp_bridge.send_message(phone, text)
        return result is not None

    logger.warning("No delivery path for channel=%s phone=%s tg=%s", channel, phone, telegram_chat_id)
    return False