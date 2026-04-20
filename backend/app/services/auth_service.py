from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


async def register(data: RegisterRequest, session: AsyncSession) -> TokenResponse:
    existing = await session.scalar(select(User).where(User.email == data.email))
    if existing:
        raise ConflictError("Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    session.add(user)
    await session.flush()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


async def login(data: LoginRequest, session: AsyncSession) -> TokenResponse:
    user = await session.scalar(
        select(User).where(User.email == data.email, User.deleted_at.is_(None))
    )
    if not user or not verify_password(data.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    user.last_login_at = datetime.now(UTC)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
