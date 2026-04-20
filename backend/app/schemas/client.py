import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=7, max_length=30)
    email: str | None = None
    birth_date: date | None = None
    tags: list[str] = []


class ClientUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    birth_date: date | None = None
    tags: list[str] | None = None


class ClientOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    team_id: uuid.UUID
    full_name: str
    phone: str
    email: str | None
    birth_date: date | None
    telegram_username: str | None
    whatsapp_opted_in: bool
    total_visits: int
    total_spent: Decimal
    last_visit_at: datetime | None
    source: str
    tags: list[str]
    created_at: datetime
