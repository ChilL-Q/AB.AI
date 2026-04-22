from fastapi import APIRouter

from app.core.deps import CurrentUserDep
from app.schemas.user import UserOut

router = APIRouter()


@router.get("", response_model=UserOut)
async def me(user: CurrentUserDep) -> UserOut:
    return UserOut.model_validate(user)
