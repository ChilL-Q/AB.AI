"""AI-agent configuration + on-demand draft endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.deps import CurrentUserDep, SessionDep
from app.core.exceptions import ForbiddenError
from app.realtime.bus import publish_nowait
from app.realtime.events import RealtimeEvent
from app.schemas.ai_agent import (
    AIAgentConfigOut,
    AIAgentConfigUpdate,
    AISuggestionOut,
)
from app.schemas.outreach import OutreachActionOut
from app.services import ai_agent_service, outreach_service

router = APIRouter()


class TriggerOutreachRequest(BaseModel):
    client_id: uuid.UUID
    custom_message: str | None = Field(None, max_length=2000)
    custom_reason: str | None = Field(None, max_length=500)


class ApproveOutreachRequest(BaseModel):
    edited_message: str | None = Field(None, max_length=2000)


def _team_id(current_user) -> uuid.UUID:
    if current_user.team_id is None:
        raise ForbiddenError("User has no team")
    return current_user.team_id


@router.get("/config", response_model=AIAgentConfigOut)
async def get_agent_config(current_user: CurrentUserDep, session: SessionDep):
    cfg = await ai_agent_service.get_config(_team_id(current_user), session)
    return cfg


@router.patch("/config", response_model=AIAgentConfigOut)
async def update_agent_config(
    data: AIAgentConfigUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    cfg = await ai_agent_service.update_config(_team_id(current_user), data, session)
    return cfg


@router.post(
    "/conversations/{conversation_id}/suggest",
    response_model=AISuggestionOut,
)
async def suggest_reply(
    conversation_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """Generate a draft on-demand for the given conversation.

    Unlike the inbound-triggered flow, this is synchronous (the operator
    clicked "Ask AI" and is waiting). We also echo the draft over WS so
    other operators looking at the same thread see the same suggestion.
    """
    team_id = _team_id(current_user)
    try:
        text = await ai_agent_service.generate_reply(
            conversation_id=conversation_id, team_id=team_id, session=session
        )
    except ai_agent_service.AIAgentError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    publish_nowait(
        RealtimeEvent(
            type="ai.suggestion",
            team_id=team_id,
            conversation_id=conversation_id,
            payload={"text": text},
            ts=datetime.now(UTC),
        )
    )
    return AISuggestionOut(conversation_id=conversation_id, text=text)


@router.get("/outreach", response_model=list[OutreachActionOut])
async def list_outreach_actions(
    current_user: CurrentUserDep,
    session: SessionDep,
    limit: int = Query(50, ge=1, le=200),
):
    return await outreach_service.get_outreach_actions(_team_id(current_user), session, limit)


@router.get("/outreach/metrics")
async def get_outreach_metrics(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await outreach_service.get_outreach_metrics(_team_id(current_user), session)


@router.post("/outreach/trigger", response_model=OutreachActionOut, status_code=201)
async def trigger_outreach(
    data: TriggerOutreachRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await outreach_service.trigger_outreach(
        _team_id(current_user),
        data.client_id,
        session,
        custom_message=data.custom_message,
        custom_reason=data.custom_reason,
    )


@router.post("/outreach/{attempt_id}/approve", response_model=OutreachActionOut)
async def approve_outreach_attempt(
    attempt_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
    data: ApproveOutreachRequest | None = None,
):
    return await outreach_service.approve_outreach(
        attempt_id, session, edited_message=data.edited_message if data else None
    )


@router.post("/outreach/{attempt_id}/reject", status_code=204)
async def reject_outreach_attempt(
    attempt_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    await outreach_service.reject_outreach(attempt_id, session)
