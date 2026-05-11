import uuid

from fastapi import APIRouter, Query

from app.core.deps import CurrentUserDep, SessionDep
from app.core.exceptions import ForbiddenError
from app.schemas.common import PaginatedResponse
from app.schemas.visit import VisitCreate, VisitOut, VisitUpdate
from app.services import visit_service

router = APIRouter()


def _team_id(current_user) -> uuid.UUID:
    if current_user.team_id is None:
        raise ForbiddenError("User has no team")
    return current_user.team_id


@router.get("", response_model=PaginatedResponse[VisitOut])
async def list_visits(
    current_user: CurrentUserDep,
    session: SessionDep,
    client_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    return await visit_service.get_visits(_team_id(current_user), client_id, session, page, limit)


@router.post("", response_model=VisitOut, status_code=201)
async def create_visit(
    data: VisitCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await visit_service.create_visit(_team_id(current_user), data, session)


@router.get("/{visit_id}", response_model=VisitOut)
async def get_visit(
    visit_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await visit_service.get_visit(_team_id(current_user), visit_id, session)


@router.patch("/{visit_id}", response_model=VisitOut)
async def update_visit(
    visit_id: uuid.UUID,
    data: VisitUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await visit_service.update_visit(_team_id(current_user), visit_id, data, session)


@router.delete("/{visit_id}", status_code=204)
async def delete_visit(
    visit_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    await visit_service.delete_visit(_team_id(current_user), visit_id, session)
