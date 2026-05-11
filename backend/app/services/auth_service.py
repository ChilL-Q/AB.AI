import logging
import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    _create_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.db.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)

logger = logging.getLogger(__name__)


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

    tokens = TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )

    await _send_verification_email(user.email, str(user.id))

    return tokens


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


async def refresh_token(data: RefreshRequest, session: AsyncSession) -> TokenResponse:
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user = await session.scalar(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    if not user:
        raise UnauthorizedError("User not found")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


async def request_password_reset(data: PasswordResetRequest, session: AsyncSession) -> dict:
    user = await session.scalar(select(User).where(User.email == data.email))
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}

    reset_token = _create_token(
        {"sub": str(user.id), "type": "password_reset", "jti": str(_uuid.uuid4())},
        expires_minutes=60,
    )

    await _send_password_reset_email(user.email, reset_token)

    return {"message": "If the email exists, a reset link has been sent"}


async def confirm_password_reset(data: PasswordResetConfirm, session: AsyncSession) -> dict:
    payload = decode_token(data.token)
    if not payload or payload.get("type") != "password_reset":
        raise BadRequestError("Invalid or expired reset token")

    user_id = payload.get("sub")
    if not user_id:
        raise BadRequestError("Invalid token payload")

    user = await session.scalar(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    if not user:
        raise NotFoundError("User not found")

    user.password_hash = hash_password(data.new_password)

    return {"message": "Password has been reset"}


async def request_email_verification(user_id: str, session: AsyncSession) -> dict:
    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise NotFoundError("User not found")

    if user.email_verified_at:
        return {"message": "Email already verified"}

    await _send_verification_email(user.email, str(user.id))
    return {"message": "Verification email sent"}


async def verify_email(token: str, session: AsyncSession) -> dict:
    payload = decode_token(token)
    if not payload or payload.get("type") != "email_verification":
        raise BadRequestError("Invalid or expired verification token")

    user_id = payload.get("sub")
    if not user_id:
        raise BadRequestError("Invalid token payload")

    user = await session.scalar(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    if not user:
        raise NotFoundError("User not found")

    if user.email_verified_at:
        return {"message": "Email already verified"}

    user.email_verified_at = datetime.now(UTC)

    return {"message": "Email verified"}


async def _send_verification_email(to: str, user_id: str) -> None:
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — skipping verification email to %s", to)
        return

    verify_token = _create_token(
        {"sub": str(user_id), "type": "email_verification", "jti": str(_uuid.uuid4())},
        expires_minutes=60 * 24,
    )

    verify_url = f"{settings.app_url}/verify-email?token={verify_token}"

    import resend

    resend.api_key = settings.resend_api_key
    try:
        resend.Emails.send(
            {
                "from": f"AB-AI <{settings.email_from}>",
                "to": [to],
                "subject": "Подтвердите ваш email — AB-AI.kz",
                "html": (
                    f"<h2>Подтверждение email</h2>"
                    f"<p>Нажмите на ссылку ниже, чтобы подтвердить ваш email:</p>"
                    f'<p><a href="{verify_url}" style="background:#F59E0B;color:#fff;padding:12px 24px;'
                    f'border-radius:8px;text-decoration:none;display:inline-block;">Подтвердить email</a></p>'
                    f"<p>Ссылка действительна 24 часа.</p>"
                    f"<p>Если вы не регистрировались на AB-AI.kz, проигнорируйте это письмо.</p>"
                ),
            }
        )
    except Exception:
        logger.exception("Failed to send verification email to %s", to)


async def _send_password_reset_email(to: str, token: str) -> None:
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — skipping reset email to %s", to)
        return

    reset_url = f"{settings.app_url}/reset-password?token={token}"

    import resend

    resend.api_key = settings.resend_api_key
    try:
        resend.Emails.send(
            {
                "from": f"AB-AI <{settings.email_from}>",
                "to": [to],
                "subject": "Сброс пароля — AB-AI.kz",
                "html": (
                    f"<h2>Сброс пароля</h2>"
                    f"<p>Нажмите на ссылку ниже, чтобы установить новый пароль:</p>"
                    f'<p><a href="{reset_url}" style="background:#F59E0B;color:#fff;padding:12px 24px;'
                    f'border-radius:8px;text-decoration:none;display:inline-block;">Сбросить пароль</a></p>'
                    f"<p>Ссылка действительна 1 час.</p>"
                    f"<p>Если вы не запрашивали сброс пароля, проигнорируйте это письмо.</p>"
                ),
            }
        )
    except Exception:
        logger.exception("Failed to send password reset email to %s", to)