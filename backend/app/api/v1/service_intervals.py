"""Service interval CRUD endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.deps import CurrentUserDep, SessionDep
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.models.service_interval import ServiceInterval
from sqlalchemy import select

router = APIRouter()


def _team_id(current_user) -> uuid.UUID:
    if current_user.team_id is None:
        raise ForbiddenError("User has no team")
    return current_user.team_id


class ServiceIntervalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    interval_value: int = Field(gt=0)
    interval_unit: str = Field(pattern="^(km|days|months)$")
    is_active: bool = True


class ServiceIntervalUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    interval_value: int | None = Field(default=None, gt=0)
    interval_unit: str | None = Field(default=None, pattern="^(km|days|months)$")
    is_active: bool | None = None


class ServiceIntervalOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    team_id: uuid.UUID
    name: str
    description: str | None
    interval_value: int
    interval_unit: str
    is_active: bool


@router.get("", response_model=list[ServiceIntervalOut])
async def list_service_intervals(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    rows = await session.execute(
        select(ServiceInterval)
        .where(ServiceInterval.team_id == _team_id(current_user))
        .order_by(ServiceInterval.name)
    )
    return rows.scalars().all()


@router.post("", response_model=ServiceIntervalOut, status_code=201)
async def create_service_interval(
    data: ServiceIntervalCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    si = ServiceInterval(team_id=_team_id(current_user), **data.model_dump())
    session.add(si)
    await session.flush()
    return si


@router.patch("/{interval_id}", response_model=ServiceIntervalOut)
async def update_service_interval(
    interval_id: uuid.UUID,
    data: ServiceIntervalUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    si = await session.scalar(
        select(ServiceInterval).where(
            ServiceInterval.id == interval_id,
            ServiceInterval.team_id == _team_id(current_user),
        )
    )
    if not si:
        raise NotFoundError("Service interval not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(si, k, v)
    await session.flush()
    return si


@router.delete("/{interval_id}", status_code=204)
async def delete_service_interval(
    interval_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    si = await session.scalar(
        select(ServiceInterval).where(
            ServiceInterval.id == interval_id,
            ServiceInterval.team_id == _team_id(current_user),
        )
    )
    if not si:
        raise NotFoundError("Service interval not found")
    await session.delete(si)


@router.get("/due", response_model=list[dict])
async def get_due_services(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    from app.services.service_reminder import get_due_services
    return await get_due_services(_team_id(current_user), session)