import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.template import Template
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.template import TemplateCreate, TemplateOut, TemplateUpdate


async def get_templates(
    team_id: uuid.UUID,
    session: AsyncSession,
    page: int = 1,
    limit: int = 50,
    category: str | None = None,
) -> PaginatedResponse[TemplateOut]:
    query = select(Template).where(
        (Template.team_id == team_id) | (Template.team_id.is_(None))
    )
    if category:
        query = query.where(Template.category == category)

    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.scalars(query.offset((page - 1) * limit).limit(limit))
    data = [TemplateOut.model_validate(t) for t in rows]
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(
            total=total or 0,
            page=page,
            limit=limit,
            has_next=(page * limit) < (total or 0),
        ),
    )


async def create_template(
    team_id: uuid.UUID, data: TemplateCreate, session: AsyncSession
) -> TemplateOut:
    template = Template(team_id=team_id, **data.model_dump())
    session.add(template)
    await session.flush()
    return TemplateOut.model_validate(template)


async def get_template(
    team_id: uuid.UUID, template_id: uuid.UUID, session: AsyncSession
) -> TemplateOut:
    template = await session.scalar(
        select(Template).where(
            Template.id == template_id,
            (Template.team_id == team_id) | (Template.team_id.is_(None)),
        )
    )
    if not template:
        raise NotFoundError("Template not found")
    return TemplateOut.model_validate(template)


async def update_template(
    team_id: uuid.UUID, template_id: uuid.UUID, data: TemplateUpdate, session: AsyncSession
) -> TemplateOut:
    template = await session.scalar(
        select(Template).where(
            Template.id == template_id,
            Template.team_id == team_id,
        )
    )
    if not template:
        raise NotFoundError("Template not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(template, field, value)

    return TemplateOut.model_validate(template)


async def delete_template(
    team_id: uuid.UUID, template_id: uuid.UUID, session: AsyncSession
) -> None:
    template = await session.scalar(
        select(Template).where(
            Template.id == template_id,
            Template.team_id == team_id,
        )
    )
    if not template:
        raise NotFoundError("Template not found")

    await session.delete(template)