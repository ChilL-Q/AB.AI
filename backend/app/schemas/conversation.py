import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ConversationChannel = Literal["whatsapp", "telegram", "sms"]
ConversationStatus = Literal["active", "resolved", "escalated"]


class ConversationCreate(BaseModel):
    client_id: uuid.UUID
    channel: ConversationChannel


class ConversationUpdate(BaseModel):
    status: ConversationStatus | None = None
    channel: ConversationChannel | None = None


class ClientMini(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    full_name: str
    phone: str
    email: str | None = None


class ConversationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    team_id: uuid.UUID
    client_id: uuid.UUID
    channel: str
    status: str
    last_message_at: datetime | None
    created_at: datetime
    client: ClientMini | None = None
    last_message_preview: str | None = None
    unread_count: int = 0


class MessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    media_url: str | None = None


class MessageOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    conversation_id: uuid.UUID
    direction: str
    text: str | None
    media_url: str | None
    status: str
    sent_by: str
    user_id: uuid.UUID | None
    sent_at: datetime | None
    delivered_at: datetime | None
    read_at: datetime | None
    created_at: datetime


class MessagePublicOut(BaseModel):
    """Narrowed Message projection for public surfaces (client widget,
    webhook echoes). Omits internal fields like user_id and external_id."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    conversation_id: uuid.UUID
    direction: str
    text: str | None
    media_url: str | None
    sent_by: str
    sent_at: datetime | None
    created_at: datetime
