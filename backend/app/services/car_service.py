import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.car import Car
from app.db.models.client import Client
from app.schemas.car import CarCreate, CarOut, CarUpdate
from app.schemas.common import PaginatedResponse, PaginationMeta


async def get_cars(
    team_id: uuid.UUID,
    client_id: uuid.UUID,
    session: AsyncSession,
    page: int = 1,
    limit: int = 50,
) -> PaginatedResponse[CarOut]:
    query = (
        select(Car)
        .join(Client)
        .where(Client.team_id == team_id, Car.client_id == client_id, Client.deleted_at.is_(None))
    )

    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.scalars(query.offset((page - 1) * limit).limit(limit))

    data = [CarOut.model_validate(c) for c in rows]
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(
            total=total or 0,
            page=page,
            limit=limit,
            has_next=(page * limit) < (total or 0),
        ),
    )


async def create_car(
    team_id: uuid.UUID, client_id: uuid.UUID, data: CarCreate, session: AsyncSession
) -> CarOut:
    client = await session.scalar(
        select(Client).where(
            Client.id == client_id, Client.team_id == team_id, Client.deleted_at.is_(None)
        )
    )
    if not client:
        raise NotFoundError("Client not found")

    car = Car(client_id=client_id, **data.model_dump())
    session.add(car)
    await session.flush()
    return CarOut.model_validate(car)


async def get_car(team_id: uuid.UUID, car_id: uuid.UUID, session: AsyncSession) -> CarOut:
    car = await session.scalar(
        select(Car)
        .join(Client)
        .where(Car.id == car_id, Client.team_id == team_id, Client.deleted_at.is_(None))
    )
    if not car:
        raise NotFoundError("Car not found")
    return CarOut.model_validate(car)


async def update_car(
    team_id: uuid.UUID, car_id: uuid.UUID, data: CarUpdate, session: AsyncSession
) -> CarOut:
    car = await session.scalar(
        select(Car)
        .join(Client)
        .where(Car.id == car_id, Client.team_id == team_id, Client.deleted_at.is_(None))
    )
    if not car:
        raise NotFoundError("Car not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(car, field, value)

    return CarOut.model_validate(car)


async def delete_car(team_id: uuid.UUID, car_id: uuid.UUID, session: AsyncSession) -> None:
    car = await session.scalar(
        select(Car)
        .join(Client)
        .where(Car.id == car_id, Client.team_id == team_id, Client.deleted_at.is_(None))
    )
    if not car:
        raise NotFoundError("Car not found")

    await session.delete(car)
