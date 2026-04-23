import uuid

from fastapi import APIRouter, Query, Request

from app.core.deps import CurrentUserDep, SessionDep
from app.core.exceptions import ForbiddenError
from app.core.limiter import limiter
from app.schemas.common import PaginatedResponse
from app.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
    MessageCreate,
    MessageOut,
)
from app.services import conversation_service

router = APIRouter()


def _team_id(current_user) -> uuid.UUID:
    if current_user.team_id is None:
        raise ForbiddenError("User has no team")
    return current_user.team_id


@router.get("", response_model=PaginatedResponse[ConversationOut])
async def list_conversations(
    current_user: CurrentUserDep,
    session: SessionDep,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None),
    status: str | None = Query(None),
):
    return await conversation_service.list_conversations(
        _team_id(current_user), session, page, limit, search, status
    )


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await conversation_service.create_conversation(_team_id(current_user), data, session)


@router.get("/by-client/{client_id}", response_model=list[ConversationOut])
async def list_conversations_by_client(
    client_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await conversation_service.list_conversations_by_client(
        _team_id(current_user), client_id, session
    )


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await conversation_service.get_conversation(
        _team_id(current_user), conversation_id, session
    )


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def update_conversation(
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await conversation_service.update_conversation(
        _team_id(current_user), conversation_id, data, session
    )


@router.get("/{conversation_id}/messages", response_model=PaginatedResponse[MessageOut])
async def list_messages(
    conversation_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
):
    return await conversation_service.list_messages(
        _team_id(current_user), conversation_id, session, page, limit
    )


@router.post("/{conversation_id}/read", response_model=ConversationOut)
async def mark_conversation_read(
    conversation_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await conversation_service.mark_conversation_read(
        _team_id(current_user), conversation_id, session
    )


@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=201)
@limiter.limit("30/minute")
async def send_message(
    request: Request,  # noqa: ARG001 — required by slowapi key_func
    conversation_id: uuid.UUID,
    data: MessageCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await conversation_service.send_message(
        _team_id(current_user), conversation_id, current_user.id, data, session
    )
