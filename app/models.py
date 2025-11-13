from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Bot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    channel: str = "telegram"          # на будущее: whatsapp, instagram, web
    token_masked: str | None = None    # последний 4 символа токена
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bot_id: int
    user_id: str
    role: str  # "user" | "assistant" | "system"
    text: str
    ts: datetime = Field(default_factory=datetime.utcnow)
    revenue_cents: int = 0              # для грубого ROI (можно оставлять 0)
    campaign: str | None = None         # для сегментации
