from fastapi import APIRouter

from app.core.deps import CurrentUserDep, SessionDep
from app.schemas.user import UserOut, UserUpdate
from app.services import user_service

router = APIRouter()


@router.get("", response_model=UserOut)
async def me(user: CurrentUserDep) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("", response_model=UserOut)
async def update_me(data: UserUpdate, user: CurrentUserDep, session: SessionDep) -> UserOut:
    return await user_service.update_profile(user.id, data, session)


@router.get("/team-members", response_model=list[UserOut])
async def team_members(user: CurrentUserDep, session: SessionDep) -> list[UserOut]:
    if user.team_id is None:
        return []
    return await user_service.get_team_members(user.team_id, session)