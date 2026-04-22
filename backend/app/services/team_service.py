from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.team import Team
from app.db.models.user import User
from app.schemas.team import TeamCreate, TeamOut, TeamUpdate


async def create_team(user: User, data: TeamCreate, session: AsyncSession) -> TeamOut:
    if user.team_id is not None:
        raise ConflictError("User already belongs to a team")

    existing = await session.scalar(select(Team).where(Team.slug == data.slug))
    if existing:
        raise ConflictError("Slug already taken")

    team = Team(
        name=data.name,
        slug=data.slug,
        timezone=data.timezone,
        locale=data.locale,
        onboarding_completed=True,
    )
    session.add(team)
    await session.flush()

    user.team_id = team.id
    user.role = "owner"
    await session.flush()

    return TeamOut.model_validate(team)


async def get_current_team(user: User, session: AsyncSession) -> TeamOut:
    if user.team_id is None:
        raise NotFoundError("User has no team")
    team = await session.get(Team, user.team_id)
    if team is None:
        raise NotFoundError("Team not found")
    return TeamOut.model_validate(team)


async def update_current_team(user: User, data: TeamUpdate, session: AsyncSession) -> TeamOut:
    if user.team_id is None:
        raise NotFoundError("User has no team")
    team = await session.get(Team, user.team_id)
    if team is None:
        raise NotFoundError("Team not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(team, field, value)
    await session.flush()
    return TeamOut.model_validate(team)
