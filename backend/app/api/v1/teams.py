from fastapi import APIRouter, status

from app.core.deps import CurrentUserDep, SessionDep
from app.schemas.team import TeamCreate, TeamOut, TeamUpdate
from app.services import team_service

router = APIRouter()


@router.get("", response_model=TeamOut)
async def get_team(user: CurrentUserDep, session: SessionDep) -> TeamOut:
    return await team_service.get_current_team(user, session)


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
async def create_team(data: TeamCreate, user: CurrentUserDep, session: SessionDep) -> TeamOut:
    return await team_service.create_team(user, data, session)


@router.patch("", response_model=TeamOut)
async def update_team(data: TeamUpdate, user: CurrentUserDep, session: SessionDep) -> TeamOut:
    return await team_service.update_current_team(user, data, session)
