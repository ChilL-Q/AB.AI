import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
    timezone: str = Field(default="Asia/Almaty", max_length=50)
    locale: str = Field(default="ru", max_length=10)


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    timezone: str | None = Field(default=None, max_length=50)
    locale: str | None = Field(default=None, max_length=10)
    onboarding_completed: bool | None = None


class TeamOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    timezone: str
    locale: str
    onboarding_completed: bool
    created_at: datetime
