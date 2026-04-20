import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.client import Client
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.utils.phone import normalize_phone


async def get_clients(
    team_id: uuid.UUID,
    session: AsyncSession,
    page: int = 1,
    limit: int = 50,
    search: str | None = None,
) -> PaginatedResponse[ClientOut]:
    query = select(Client).where(Client.team_id == team_id, Client.deleted_at.is_(None))

    if search:
        like = f"%{search}%"
        query = query.where(
            or_(
                Client.full_name.ilike(like),
                Client.phone.ilike(like),
                Client.email.ilike(like),
            )
        )

    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.scalars(query.offset((page - 1) * limit).limit(limit))

    data = [ClientOut.model_validate(c) for c in rows]
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(
            total=total or 0,
            page=page,
            limit=limit,
            has_next=(page * limit) < (total or 0),
        ),
    )


async def create_client(team_id: uuid.UUID, data: ClientCreate, session: AsyncSession) -> ClientOut:
    phone = normalize_phone(data.phone)
    existing = await session.scalar(
        select(Client).where(
            Client.team_id == team_id,
            Client.phone == phone,
            Client.deleted_at.is_(None),
        )
    )
    if existing:
        raise ConflictError("Client with this phone already exists")

    client = Client(team_id=team_id, **data.model_dump(), phone=phone)
    session.add(client)
    await session.flush()
    return ClientOut.model_validate(client)


async def get_client(team_id: uuid.UUID, client_id: uuid.UUID, session: AsyncSession) -> ClientOut:
    client = await session.scalar(
        select(Client).where(
            Client.id == client_id, Client.team_id == team_id, Client.deleted_at.is_(None)
        )
    )
    if not client:
        raise NotFoundError("Client not found")
    return ClientOut.model_validate(client)


async def update_client(
    team_id: uuid.UUID, client_id: uuid.UUID, data: ClientUpdate, session: AsyncSession
) -> ClientOut:
    client = await session.scalar(
        select(Client).where(
            Client.id == client_id, Client.team_id == team_id, Client.deleted_at.is_(None)
        )
    )
    if not client:
        raise NotFoundError("Client not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(client, field, value)

    return ClientOut.model_validate(client)


async def delete_client(team_id: uuid.UUID, client_id: uuid.UUID, session: AsyncSession) -> None:
    from datetime import UTC, datetime

    client = await session.scalar(
        select(Client).where(
            Client.id == client_id, Client.team_id == team_id, Client.deleted_at.is_(None)
        )
    )
    if not client:
        raise NotFoundError("Client not found")

    client.deleted_at = datetime.now(UTC)
