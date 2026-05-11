import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    type: str = Field(pattern="^(one_time|recurring|triggered)$")
    channels: list[str] = Field(default_factory=list)
    schedule: dict = Field(default_factory=dict)
    trigger: dict = Field(default_factory=dict)
    template_id: uuid.UUID | None = None
    ab_test_config: dict | None = None


class CampaignUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    type: str | None = Field(None, pattern="^(one_time|recurring|triggered)$")
    status: str | None = Field(None, pattern="^(draft|running|paused|completed|archived)$")
    channels: list[str] | None = None
    schedule: dict | None = None
    trigger: dict | None = None
    template_id: uuid.UUID | None = None
    ab_test_config: dict | None = None


class CampaignOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    team_id: uuid.UUID
    created_by: uuid.UUID
    name: str
    description: str | None
    type: str
    status: str
    trigger: dict
    channels: list[str]
    schedule: dict
    template_id: uuid.UUID | None
    stats: dict
    ab_test_config: dict | None
    created_at: datetime
    updated_at: datetime | None = None