"""Pydantic schemas for the AI-agent module.

Three shapes:
  - AIAgentConfigOut: the current team's configuration (always returned
    via lazy-create, so the frontend never has to special-case 404).
  - AIAgentConfigUpdate: PATCH body. All fields optional; validation is
    tight on `mode` (enum) but lenient on free-form text so owners can
    experiment with personality/tone wording.
  - AISuggestionOut: on-demand draft produced by the AI — used as the
    body of `ai.suggestion` realtime events and as the response of the
    manual "ask AI" endpoint.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AgentModeLiteral = Literal["auto", "semi_auto", "manual"]


class AIAgentConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID
    mode: AgentModeLiteral
    personality: str | None = None
    tone: str
    knowledge_base: dict = Field(default_factory=dict)
    forbidden_topics: list[str] = Field(default_factory=list)
    escalation_rules: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class AIAgentConfigUpdate(BaseModel):
    mode: AgentModeLiteral | None = None
    personality: str | None = Field(default=None, max_length=4000)
    tone: str | None = Field(default=None, max_length=200)
    knowledge_base: dict | None = None
    forbidden_topics: list[str] | None = None
    escalation_rules: dict | None = None


class AISuggestionOut(BaseModel):
    conversation_id: uuid.UUID
    text: str
