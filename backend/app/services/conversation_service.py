import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.db.models.client import Client
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
    MessageCreate,
    MessageOut,
)


async def _load_conversation(
    team_id: uuid.UUID, conversation_id: uuid.UUID, session: AsyncSession
) -> Conversation:
    conv = await session.scalar(
        select(Conversation)
        .options(selectinload(Conversation.client))
        .where(Conversation.id == conversation_id, Conversation.team_id == team_id)
    )
    if not conv:
        raise NotFoundError("Conversation not found")
    return conv


def _to_out(conv: Conversation, last_preview: str | None = None) -> ConversationOut:
    return ConversationOut.model_validate(
        {
            "id": conv.id,
            "team_id": conv.team_id,
            "client_id": conv.client_id,
            "channel": conv.channel,
            "status": conv.status,
            "last_message_at": conv.last_message_at,
            "created_at": conv.created_at,
            "client": conv.client,
            "last_message_preview": last_preview,
            "unread_count": 0,
        }
    )


async def list_conversations(
    team_id: uuid.UUID,
    session: AsyncSession,
    page: int = 1,
    limit: int = 50,
    search: str | None = None,
    status: str | None = None,
) -> PaginatedResponse[ConversationOut]:
    query = (
        select(Conversation)
        .options(selectinload(Conversation.client))
        .where(Conversation.team_id == team_id)
    )
    if status:
        query = query.where(Conversation.status == status)
    if search:
        like = f"%{search}%"
        query = query.join(Client, Conversation.client_id == Client.id).where(
            or_(Client.full_name.ilike(like), Client.phone.ilike(like))
        )

    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    query = query.order_by(
        Conversation.last_message_at.desc().nulls_last(),
        Conversation.created_at.desc(),
    )
    rows = (await session.scalars(query.offset((page - 1) * limit).limit(limit))).all()

    # fetch last message preview for listed conversations
    previews: dict[uuid.UUID, str] = {}
    if rows:
        ids = [c.id for c in rows]
        sub = (
            select(
                Message.conversation_id,
                Message.text,
                func.row_number()
                .over(partition_by=Message.conversation_id, order_by=Message.created_at.desc())
                .label("rn"),
            )
            .where(Message.conversation_id.in_(ids))
            .subquery()
        )
        res = await session.execute(select(sub.c.conversation_id, sub.c.text).where(sub.c.rn == 1))
        for cid, text in res.all():
            previews[cid] = text or ""

    data = [_to_out(c, previews.get(c.id)) for c in rows]
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(total=total, page=page, limit=limit, has_next=page * limit < total),
    )


async def create_conversation(
    team_id: uuid.UUID, data: ConversationCreate, session: AsyncSession
) -> ConversationOut:
    client = await session.scalar(
        select(Client).where(
            Client.id == data.client_id, Client.team_id == team_id, Client.deleted_at.is_(None)
        )
    )
    if not client:
        raise NotFoundError("Client not found")

    conv = Conversation(
        team_id=team_id,
        client_id=data.client_id,
        channel=data.channel,
        status="active",
    )
    session.add(conv)
    await session.flush()
    await session.refresh(conv, attribute_names=["client"])
    return _to_out(conv)


async def get_conversation(
    team_id: uuid.UUID, conversation_id: uuid.UUID, session: AsyncSession
) -> ConversationOut:
    conv = await _load_conversation(team_id, conversation_id, session)
    return _to_out(conv)


async def update_conversation(
    team_id: uuid.UUID,
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    session: AsyncSession,
) -> ConversationOut:
    conv = await _load_conversation(team_id, conversation_id, session)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(conv, field, value)
    return _to_out(conv)


async def list_messages(
    team_id: uuid.UUID,
    conversation_id: uuid.UUID,
    session: AsyncSession,
    page: int = 1,
    limit: int = 100,
) -> PaginatedResponse[MessageOut]:
    await _load_conversation(team_id, conversation_id, session)
    base = select(Message).where(Message.conversation_id == conversation_id)
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = (
        await session.scalars(
            base.order_by(Message.created_at.asc()).offset((page - 1) * limit).limit(limit)
        )
    ).all()
    return PaginatedResponse(
        data=[MessageOut.model_validate(m) for m in rows],
        meta=PaginationMeta(total=total, page=page, limit=limit, has_next=page * limit < total),
    )


async def send_message(
    team_id: uuid.UUID,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    data: MessageCreate,
    session: AsyncSession,
) -> MessageOut:
    conv = await _load_conversation(team_id, conversation_id, session)
    now = datetime.now(UTC)
    msg = Message(
        conversation_id=conv.id,
        direction="outbound",
        text=data.text,
        media_url=data.media_url,
        status="sent",
        sent_by="human",
        user_id=user_id,
        sent_at=now,
    )
    session.add(msg)
    conv.last_message_at = now
    await session.flush()
    return MessageOut.model_validate(msg)
