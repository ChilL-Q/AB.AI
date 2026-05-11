import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.client import Client
from app.db.models.visit import Visit
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.visit import VisitCreate, VisitOut, VisitUpdate


async def get_visits(
    team_id: uuid.UUID,
    client_id: uuid.UUID | None,
    session: AsyncSession,
    page: int = 1,
    limit: int = 50,
) -> PaginatedResponse[VisitOut]:
    query = select(Visit).where(Visit.team_id == team_id)

    if client_id:
        query = query.where(Visit.client_id == client_id)

    query = query.order_by(Visit.visited_at.desc())

    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.scalars(query.offset((page - 1) * limit).limit(limit))

    data = [VisitOut.model_validate(v) for v in rows]
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(
            total=total or 0,
            page=page,
            limit=limit,
            has_next=(page * limit) < (total or 0),
        ),
    )


async def create_visit(team_id: uuid.UUID, data: VisitCreate, session: AsyncSession) -> VisitOut:
    client = await session.scalar(
        select(Client).where(
            Client.id == data.client_id, Client.team_id == team_id, Client.deleted_at.is_(None)
        )
    )
    if not client:
        raise NotFoundError("Client not found")

    services_payload = [
        {k: (float(v) if isinstance(v, Decimal) else v) for k, v in s.model_dump().items()}
        for s in data.services
    ]

    visit = Visit(
        team_id=team_id,
        client_id=data.client_id,
        car_id=data.car_id,
        mechanic_id=data.mechanic_id,
        visited_at=data.visited_at,
        total_amount=data.total_amount,
        services=services_payload,
        notes=data.notes,
        source=data.source,
    )
    session.add(visit)

    client.total_visits += 1
    client.total_spent += data.total_amount
    if not client.last_visit_at or data.visited_at > client.last_visit_at:
        client.last_visit_at = data.visited_at

    # Attribution: if this client had a pending/sent outreach attempt,
    # mark it as resulted in a visit and attribute revenue.
    from app.db.models.outreach_attempt import OutreachAttempt

    outreach = await session.scalar(
        select(OutreachAttempt).where(
            OutreachAttempt.client_id == data.client_id,
            OutreachAttempt.team_id == team_id,
            OutreachAttempt.status.in_(["sent", "replied"]),
            OutreachAttempt.resulted_in_visit.is_(False),
        )
    )
    if outreach:
        outreach.resulted_in_visit = True
        outreach.resulted_in_revenue = data.total_amount

    await session.flush()
    return VisitOut.model_validate(visit)


async def get_visit(team_id: uuid.UUID, visit_id: uuid.UUID, session: AsyncSession) -> VisitOut:
    visit = await session.scalar(
        select(Visit).where(Visit.id == visit_id, Visit.team_id == team_id)
    )
    if not visit:
        raise NotFoundError("Visit not found")
    return VisitOut.model_validate(visit)


async def update_visit(
    team_id: uuid.UUID, visit_id: uuid.UUID, data: VisitUpdate, session: AsyncSession
) -> VisitOut:
    visit = await session.scalar(
        select(Visit).where(Visit.id == visit_id, Visit.team_id == team_id)
    )
    if not visit:
        raise NotFoundError("Visit not found")

    update_data = data.model_dump(exclude_none=True)
    if data.services is not None:
        update_data["services"] = [
            {k: (float(v) if isinstance(v, Decimal) else v) for k, v in s.model_dump().items()}
            for s in data.services
        ]

    for field, value in update_data.items():
        setattr(visit, field, value)

    return VisitOut.model_validate(visit)


async def delete_visit(team_id: uuid.UUID, visit_id: uuid.UUID, session: AsyncSession) -> None:
    visit = await session.scalar(
        select(Visit).where(Visit.id == visit_id, Visit.team_id == team_id)
    )
    if not visit:
        raise NotFoundError("Visit not found")

    client = await session.scalar(
        select(Client).where(Client.id == visit.client_id, Client.team_id == team_id)
    )
    if client:
        client.total_visits = max(0, client.total_visits - 1)
        client.total_spent = max(0, client.total_spent - visit.total_amount)
        if client.total_visits == 0:
            client.last_visit_at = None

    await session.delete(visit)
