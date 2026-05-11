import uuid

from fastapi import APIRouter, Query

from app.core.deps import CurrentUserDep, SessionDep
from app.core.exceptions import ForbiddenError
from app.schemas.campaign import CampaignCreate, CampaignOut, CampaignUpdate
from app.schemas.common import PaginatedResponse
from app.services import campaign_service

router = APIRouter()


def _team_id(current_user) -> uuid.UUID:
    if current_user.team_id is None:
        raise ForbiddenError("User has no team")
    return current_user.team_id


@router.get("", response_model=PaginatedResponse[CampaignOut])
async def list_campaigns(
    current_user: CurrentUserDep,
    session: SessionDep,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = Query(None),
):
    return await campaign_service.get_campaigns(
        _team_id(current_user), session, page, limit, status
    )


@router.post("", response_model=CampaignOut, status_code=201)
async def create_campaign(
    data: CampaignCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await campaign_service.create_campaign(
        _team_id(current_user), current_user.id, data, session
    )


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await campaign_service.get_campaign(
        _team_id(current_user), campaign_id, session
    )


@router.patch("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: uuid.UUID,
    data: CampaignUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await campaign_service.update_campaign(
        _team_id(current_user), campaign_id, data, session
    )


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    await campaign_service.delete_campaign(_team_id(current_user), campaign_id, session)


@router.post("/{campaign_id}/run", response_model=CampaignOut)
async def run_campaign(
    campaign_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    """Start a campaign: sets status to 'running' and dispatches execution."""
    from app.services.campaign_engine import execute_campaign
    from app.tasks.campaigns import evaluate_triggers

    campaign = await campaign_service.get_campaign(
        _team_id(current_user), campaign_id, session
    )
    if campaign.status in ("completed", "archived"):
        raise ForbiddenError("Cannot run a completed or archived campaign")

    result = await campaign_service.update_campaign(
        _team_id(current_user), campaign_id, CampaignUpdate(status="running"), session
    )

    # Dispatch async execution
    try:
        evaluate_triggers.delay()
    except Exception:
        pass

    return result