import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

OutreachStatusLiteral = Literal["pending", "sent", "replied", "escalated", "failed"]


class OutreachAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID
    client_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    status: OutreachStatusLiteral
    reason: dict = Field(default_factory=dict)
    message_text: str | None = None
    sent_at: datetime | None = None
    replied_at: datetime | None = None
    resulted_in_visit: bool = False
    resulted_in_revenue: Decimal = Decimal("0")
    created_at: datetime


class OutreachActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    client_name: str = ""
    status: OutreachStatusLiteral
    reason: dict = Field(default_factory=dict)
    message_text: str | None = None
    sent_at: datetime | None = None
    replied_at: datetime | None = None
    resulted_in_visit: bool = False
    resulted_in_revenue: Decimal = Decimal("0")
    created_at: datetime
