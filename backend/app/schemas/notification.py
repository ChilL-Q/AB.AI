import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    body: str
    data: dict = {}
    channels: list[str] = []
    read_at: datetime | None = None
    created_at: datetime