import uuid

from fastapi import APIRouter, Query

from app.core.deps import CurrentUserDep, SessionDep
from app.core.exceptions import ForbiddenError
from app.schemas.car import CarCreate, CarOut, CarUpdate
from app.schemas.common import PaginatedResponse
from app.services import car_service

router = APIRouter()


def _team_id(current_user) -> uuid.UUID:
    if current_user.team_id is None:
        raise ForbiddenError("User has no team")
    return current_user.team_id


@router.get("/client/{client_id}", response_model=PaginatedResponse[CarOut])
async def list_cars(
    client_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    return await car_service.get_cars(_team_id(current_user), client_id, session, page, limit)


@router.post("/client/{client_id}", response_model=CarOut, status_code=201)
async def create_car(
    client_id: uuid.UUID,
    data: CarCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await car_service.create_car(_team_id(current_user), client_id, data, session)


@router.get("/{car_id}", response_model=CarOut)
async def get_car(
    car_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await car_service.get_car(_team_id(current_user), car_id, session)


@router.patch("/{car_id}", response_model=CarOut)
async def update_car(
    car_id: uuid.UUID,
    data: CarUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await car_service.update_car(_team_id(current_user), car_id, data, session)


@router.delete("/{car_id}", status_code=204)
async def delete_car(
    car_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    await car_service.delete_car(_team_id(current_user), car_id, session)
