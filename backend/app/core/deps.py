from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_session

bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> UUID:
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("Invalid or expired token")
    try:
        return UUID(payload["sub"])
    except (KeyError, ValueError) as err:
        raise UnauthorizedError("Invalid token payload") from err


async def get_current_user(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from sqlalchemy import select

    from app.db.models.user import User

    result = await session.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User not found or deleted")
    return user


SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated["User", Depends(get_current_user)]  # noqa: F821
