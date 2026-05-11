import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.campaign import Campaign
from app.schemas.campaign import CampaignCreate, CampaignOut, CampaignUpdate
from app.schemas.common import PaginatedResponse, PaginationMeta


async def get_campaigns(
    team_id: uuid.UUID,
    session: AsyncSession,
    page: int = 1,
    limit: int = 50,
    status: str | None = None,
) -> PaginatedResponse[CampaignOut]:
    query = select(Campaign).where(Campaign.team_id == team_id)
    if status:
        query = query.where(Campaign.status == status)

    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.scalars(
        query.order_by(Campaign.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    data = [CampaignOut.model_validate(c) for c in rows]
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(
            total=total or 0,
            page=page,
            limit=limit,
            has_next=(page * limit) < (total or 0),
        ),
    )


async def create_campaign(
    team_id: uuid.UUID, user_id: uuid.UUID, data: CampaignCreate, session: AsyncSession
) -> CampaignOut:
    campaign = Campaign(
        team_id=team_id,
        created_by=user_id,
        **data.model_dump(),
    )
    session.add(campaign)
    await session.flush()
    return CampaignOut.model_validate(campaign)


async def get_campaign(
    team_id: uuid.UUID, campaign_id: uuid.UUID, session: AsyncSession
) -> CampaignOut:
    campaign = await session.scalar(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.team_id == team_id)
    )
    if not campaign:
        raise NotFoundError("Campaign not found")
    return CampaignOut.model_validate(campaign)


async def update_campaign(
    team_id: uuid.UUID, campaign_id: uuid.UUID, data: CampaignUpdate, session: AsyncSession
) -> CampaignOut:
    campaign = await session.scalar(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.team_id == team_id)
    )
    if not campaign:
        raise NotFoundError("Campaign not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(campaign, field, value)

    return CampaignOut.model_validate(campaign)


async def delete_campaign(
    team_id: uuid.UUID, campaign_id: uuid.UUID, session: AsyncSession
) -> None:
    campaign = await session.scalar(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.team_id == team_id)
    )
    if not campaign:
        raise NotFoundError("Campaign not found")

    await session.delete(campaign)