from fastapi import APIRouter

from app.core.deps import CurrentUserDep, SessionDep
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, session: SessionDep) -> TokenResponse:
    return await auth_service.register(data, session)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, session: SessionDep) -> TokenResponse:
    return await auth_service.login(data, session)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, session: SessionDep) -> TokenResponse:
    return await auth_service.refresh_token(data, session)


@router.post("/password-reset")
async def request_password_reset(data: PasswordResetRequest, session: SessionDep) -> dict:
    return await auth_service.request_password_reset(data, session)


@router.post("/password-reset/confirm")
async def confirm_password_reset(data: PasswordResetConfirm, session: SessionDep) -> dict:
    return await auth_service.confirm_password_reset(data, session)


@router.post("/verify-email")
async def verify_email(token: str, session: SessionDep) -> dict:
    return await auth_service.verify_email(token, session)


@router.post("/verify-email/request")
async def request_email_verification(current_user: CurrentUserDep, session: SessionDep) -> dict:
    return await auth_service.request_email_verification(str(current_user.id), session)