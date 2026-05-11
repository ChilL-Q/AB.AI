import uuid

from fastapi import APIRouter, Query

from app.core.deps import CurrentUserDep, SessionDep
from app.schemas.common import PaginatedResponse
from app.schemas.notification import NotificationOut
from app.services import notification_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[NotificationOut])
async def list_notifications(
    current_user: CurrentUserDep,
    session: SessionDep,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
):
    return await notification_service.get_notifications(current_user.id, session, page, limit, unread_only)


@router.get("/unread-count")
async def unread_count(current_user: CurrentUserDep, session: SessionDep):
    count = await notification_service.get_unread_count(current_user.id, session)
    return {"count": count}


@router.patch("/{notification_id}/read")
async def mark_read(notification_id: uuid.UUID, current_user: CurrentUserDep, session: SessionDep):
    await notification_service.mark_read(notification_id, current_user.id, session)
    return {"status": "ok"}


@router.post("/mark-all-read")
async def mark_all_read(current_user: CurrentUserDep, session: SessionDep):
    count = await notification_service.mark_all_read(current_user.id, session)
    return {"marked": count}