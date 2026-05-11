import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.user import User
from app.schemas.user import UserOut, UserUpdate


async def update_profile(user_id: uuid.UUID, data: UserUpdate, session: AsyncSession) -> UserOut:
    user = await session.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)

    return UserOut.model_validate(user)


async def get_team_members(team_id: uuid.UUID, session: AsyncSession) -> list[UserOut]:
    rows = await session.scalars(
        select(User)
        .where(User.team_id == team_id, User.deleted_at.is_(None))
        .order_by(User.created_at)
    )
    return [UserOut.model_validate(u) for u in rows]