import uuid

from fastapi import APIRouter, Query

from app.core.deps import CurrentUserDep, SessionDep
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate
from app.schemas.common import PaginatedResponse
from app.services import client_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ClientOut])
async def list_clients(
    current_user: CurrentUserDep,
    session: SessionDep,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None),
):
    return await client_service.get_clients(current_user.team_id, session, page, limit, search)


@router.post("", response_model=ClientOut, status_code=201)
async def create_client(
    data: ClientCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await client_service.create_client(current_user.team_id, data, session)


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await client_service.get_client(current_user.team_id, client_id, session)


@router.patch("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await client_service.update_client(current_user.team_id, client_id, data, session)


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    await client_service.delete_client(current_user.team_id, client_id, session)
