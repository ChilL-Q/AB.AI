import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    channels: list[str] = Field(default_factory=list)


class TemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    category: str | None = Field(None, min_length=1, max_length=100)
    content: str | None = Field(None, min_length=1)
    channels: list[str] | None = None


class TemplateOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    team_id: uuid.UUID | None
    name: str
    category: str
    content: str
    channels: list[str]
    whatsapp_template_id: str | None
    whatsapp_status: str | None
    created_at: datetime
    updated_at: datetime | None = None