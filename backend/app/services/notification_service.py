import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.notification import Notification
from app.schemas.common import PaginatedResponse, PaginationMeta


async def create_notification(
    *,
    user_id: uuid.UUID,
    type: str,
    title: str,
    body: str,
    data: dict | None = None,
    channels: list[str] | None = None,
    session: AsyncSession,
) -> Notification:
    n = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        data=data or {},
        channels=channels or ["in_app"],
    )
    session.add(n)
    await session.flush()
    await session.refresh(n)
    return n


async def get_notifications(
    user_id: uuid.UUID,
    session: AsyncSession,
    page: int = 1,
    limit: int = 50,
    unread_only: bool = False,
) -> PaginatedResponse:
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))

    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.scalars(
        query.order_by(Notification.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    items = rows.all()
    return PaginatedResponse(
        data=items,
        meta=PaginationMeta(
            total=total or 0,
            page=page,
            limit=limit,
            has_next=(page * limit) < (total or 0),
        ),
    )


async def mark_read(notification_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession) -> None:
    from datetime import UTC, datetime

    n = await session.scalar(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
    )
    if not n:
        raise NotFoundError("Notification not found")
    n.read_at = datetime.now(UTC)


async def mark_all_read(user_id: uuid.UUID, session: AsyncSession) -> int:
    from datetime import UTC, datetime

    result = await session.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    return result.rowcount


async def get_unread_count(user_id: uuid.UUID, session: AsyncSession) -> int:
    count = await session.scalar(
        select(func.count()).select_from(
            select(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .subquery()
        )
    )
    return count or 0