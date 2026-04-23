"""
Typed envelope for real-time events pushed over WebSocket.

Shape is intentionally flat/JSON-friendly: the frontend parses these as
`{ type, team_id, conversation_id, payload }` and dispatches by `type`.

All events are scoped to a team. Conversation-scoped events also carry
`conversation_id` so the client can skip dispatching for threads that
aren't open.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

EventType = Literal[
    "message.new",
    "message.read",
    "typing.start",
    "typing.stop",
    "presence.online",
    "presence.offline",
]


class RealtimeEvent(BaseModel):
    type: EventType
    team_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    payload: dict[str, Any] = {}
    ts: datetime
