import uuid

from fastapi import APIRouter, Query

from app.core.deps import CurrentUserDep, SessionDep
from app.core.exceptions import ForbiddenError
from app.schemas.common import PaginatedResponse
from app.schemas.template import TemplateCreate, TemplateOut, TemplateUpdate
from app.services import template_service

router = APIRouter()


def _team_id(current_user) -> uuid.UUID:
    if current_user.team_id is None:
        raise ForbiddenError("User has no team")
    return current_user.team_id


@router.get("", response_model=PaginatedResponse[TemplateOut])
async def list_templates(
    current_user: CurrentUserDep,
    session: SessionDep,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    category: str | None = Query(None),
):
    return await template_service.get_templates(
        _team_id(current_user), session, page, limit, category
    )


@router.post("", response_model=TemplateOut, status_code=201)
async def create_template(
    data: TemplateCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await template_service.create_template(_team_id(current_user), data, session)


@router.get("/{template_id}", response_model=TemplateOut)
async def get_template(
    template_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await template_service.get_template(_team_id(current_user), template_id, session)


@router.patch("/{template_id}", response_model=TemplateOut)
async def update_template(
    template_id: uuid.UUID,
    data: TemplateUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await template_service.update_template(
        _team_id(current_user), template_id, data, session
    )


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    await template_service.delete_template(_team_id(current_user), template_id, session)