import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.core.exceptions import NotFoundError
from app.db.models.client import Client
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.realtime.bus import publish_nowait
from app.realtime.events import RealtimeEvent
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
    MessageCreate,
    MessageOut,
    MessagePage,
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


def _to_out(
    conv: Conversation,
    last_preview: str | None = None,
    unread_count: int = 0,
) -> ConversationOut:
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
            "unread_count": unread_count,
        }
    )


async def _unread_counts(
    conversation_ids: list[uuid.UUID], session: AsyncSession
) -> dict[uuid.UUID, int]:
    """Count inbound messages newer than each conversation's last_read marker.

    For conversations without a read marker all inbound messages are unread.
    Executes as a single aggregate query over the N listed conversations.
    """
    if not conversation_ids:
        return {}
    last_read = aliased(Message)
    res = await session.execute(
        select(Conversation.id, func.count(Message.id))
        .select_from(Conversation)
        .join(Message, Message.conversation_id == Conversation.id)
        .outerjoin(last_read, Conversation.last_read_message_id == last_read.id)
        .where(
            Conversation.id.in_(conversation_ids),
            Message.direction == "inbound",
            or_(
                Conversation.last_read_message_id.is_(None),
                Message.created_at > last_read.created_at,
            ),
        )
        .group_by(Conversation.id)
    )
    return {cid: count for cid, count in res.all()}


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
                Message.media_url,
                func.row_number()
                .over(partition_by=Message.conversation_id, order_by=Message.created_at.desc())
                .label("rn"),
            )
            .where(Message.conversation_id.in_(ids))
            .subquery()
        )
        res = await session.execute(
            select(sub.c.conversation_id, sub.c.text, sub.c.media_url).where(sub.c.rn == 1)
        )
        for cid, text, media_url in res.all():
            if text:
                previews[cid] = text
            elif media_url:
                previews[cid] = "[вложение]"
            else:
                previews[cid] = ""

    unread = await _unread_counts([c.id for c in rows], session)
    data = [_to_out(c, previews.get(c.id), unread.get(c.id, 0)) for c in rows]
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

    # Idempotency: if an active conversation with the same client+channel
    # already exists for this team, return it rather than creating a duplicate.
    existing = await session.scalar(
        select(Conversation)
        .options(selectinload(Conversation.client))
        .where(
            Conversation.team_id == team_id,
            Conversation.client_id == data.client_id,
            Conversation.channel == data.channel,
            Conversation.status == "active",
        )
    )
    if existing:
        return _to_out(existing)

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


async def list_conversations_by_client(
    team_id: uuid.UUID, client_id: uuid.UUID, session: AsyncSession
) -> list[ConversationOut]:
    # Ensure the client belongs to this team before exposing its conversations.
    client = await session.scalar(
        select(Client).where(
            Client.id == client_id, Client.team_id == team_id, Client.deleted_at.is_(None)
        )
    )
    if not client:
        raise NotFoundError("Client not found")

    rows = (
        await session.scalars(
            select(Conversation)
            .options(selectinload(Conversation.client))
            .where(Conversation.team_id == team_id, Conversation.client_id == client_id)
            .order_by(
                Conversation.last_message_at.desc().nulls_last(),
                Conversation.created_at.desc(),
            )
        )
    ).all()
    return [_to_out(c) for c in rows]


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
    limit: int = 50,
    before_id: uuid.UUID | None = None,
) -> MessagePage:
    """Cursor-paginated message fetch.

    Strategy: fetch the N newest messages older than the cursor (or the N
    newest overall when no cursor is given), sorted DESC by (created_at, id),
    then reverse in Python so the returned page is oldest→newest — the shape
    the client expects to append above the current view on "load older".

    Fetching `limit + 1` lets us set `has_more` without a second COUNT query.
    """
    await _load_conversation(team_id, conversation_id, session)
    q = select(Message).where(Message.conversation_id == conversation_id)

    if before_id is not None:
        cursor_row = (
            await session.execute(
                select(Message.created_at, Message.id).where(
                    Message.id == before_id,
                    Message.conversation_id == conversation_id,
                )
            )
        ).one_or_none()
        if cursor_row is None:
            raise NotFoundError("Cursor message not found")
        cursor_ts, cursor_uuid = cursor_row
        q = q.where(tuple_(Message.created_at, Message.id) < tuple_(cursor_ts, cursor_uuid))

    rows = list(
        (
            await session.scalars(
                q.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit + 1)
            )
        ).all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    rows.reverse()  # oldest → newest for the returned page

    next_cursor = rows[0].id if has_more and rows else None
    return MessagePage(
        data=[MessageOut.model_validate(m) for m in rows],
        next_cursor=next_cursor,
        has_more=has_more,
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
    out = MessageOut.model_validate(msg)
    publish_nowait(
        RealtimeEvent(
            type="message.new",
            team_id=team_id,
            conversation_id=conv.id,
            user_id=user_id,
            payload=out.model_dump(mode="json"),
            ts=now,
        )
    )
    return out


async def mark_conversation_read(
    team_id: uuid.UUID, conversation_id: uuid.UUID, session: AsyncSession
) -> ConversationOut:
    """Mark all inbound messages in the thread as read by pinning the marker
    to the latest inbound message. Idempotent: no-op if there are no inbound
    messages, or the marker already points at the latest one."""
    conv = await _load_conversation(team_id, conversation_id, session)
    latest_inbound_id = await session.scalar(
        select(Message.id)
        .where(Message.conversation_id == conv.id, Message.direction == "inbound")
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    if latest_inbound_id and conv.last_read_message_id != latest_inbound_id:
        conv.last_read_message_id = latest_inbound_id
        await session.flush()
        publish_nowait(
            RealtimeEvent(
                type="message.read",
                team_id=team_id,
                conversation_id=conv.id,
                payload={"last_read_message_id": str(latest_inbound_id)},
                ts=datetime.now(UTC),
            )
        )
    return _to_out(conv, unread_count=0)
