"""Weekly email report service.

Sends a summary to every team owner every Monday at 9am local time:
  - How many clients AI contacted
  - How many returned
  - Revenue attributed to AI outreach
  - Top 5 clients by visit revenue
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.client import Client
from app.db.models.outreach_attempt import OutreachAttempt
from app.db.models.team import Team
from app.db.models.user import User
from app.db.models.visit import Visit
from app.db.session import AsyncSessionFactory

logger = logging.getLogger(__name__)

_env = Environment(
    loader=FileSystemLoader("app/templates/emails"),
    autoescape=True,
)


async def _get_weekly_stats(team_id: uuid.UUID, session: AsyncSession) -> dict:
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)

    total_clients = (
        await session.scalar(
            select(func.count()).select_from(
                select(Client)
                .where(Client.team_id == team_id, Client.deleted_at.is_(None))
                .subquery()
            )
        )
        or 0
    )

    new_clients = (
        await session.scalar(
            select(func.count()).select_from(
                select(Client)
                .where(
                    Client.team_id == team_id,
                    Client.deleted_at.is_(None),
                    Client.created_at >= week_ago,
                )
                .subquery()
            )
        )
        or 0
    )

    outreach_sent = (
        await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt)
                .where(
                    OutreachAttempt.team_id == team_id,
                    OutreachAttempt.sent_at >= week_ago,
                )
                .subquery()
            )
        )
        or 0
    )

    outreach_replied = (
        await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt)
                .where(
                    OutreachAttempt.team_id == team_id,
                    OutreachAttempt.replied_at >= week_ago,
                )
                .subquery()
            )
        )
        or 0
    )

    outreach_returned = (
        await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt)
                .where(
                    OutreachAttempt.team_id == team_id,
                    OutreachAttempt.resulted_in_visit.is_(True),
                )
                .subquery()
            )
        )
        or 0
    )

    outreach_revenue = await session.scalar(
        select(func.coalesce(func.sum(OutreachAttempt.resulted_in_revenue), 0)).where(
            OutreachAttempt.team_id == team_id
        )
    ) or Decimal("0")

    week_revenue = await session.scalar(
        select(func.coalesce(func.sum(Visit.total_amount), 0)).where(
            Visit.team_id == team_id,
            Visit.visited_at >= week_ago,
        )
    ) or Decimal("0")

    escalated = (
        await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt)
                .where(
                    OutreachAttempt.team_id == team_id,
                    OutreachAttempt.status == "escalated",
                )
                .subquery()
            )
        )
        or 0
    )

    top_visits = (
        await session.execute(
            select(
                Client.full_name,
                func.sum(Visit.total_amount).label("spent"),
                func.count().label("visits"),
            )
            .join(Client, Visit.client_id == Client.id)
            .where(Visit.team_id == team_id, Visit.visited_at >= week_ago)
            .group_by(Client.full_name)
            .order_by(func.sum(Visit.total_amount).desc())
            .limit(5)
        )
    ).all()

    return {
        "total_clients": total_clients,
        "new_clients": new_clients,
        "outreach_sent": outreach_sent,
        "outreach_replied": outreach_replied,
        "outreach_returned": outreach_returned,
        "outreach_revenue": float(outreach_revenue),
        "week_revenue": float(week_revenue),
        "escalated": escalated,
        "top_visits": [{"name": r[0], "spent": float(r[1]), "visits": r[2]} for r in top_visits],
    }


def _render_email(team_name: str, stats: dict) -> str:
    template = _env.get_template("weekly_report.html")
    return template.render(team_name=team_name, now=datetime.now(UTC), **stats)


async def _send_email(to: str, team_name: str, stats: dict) -> None:
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — skipping email to %s", to)
        return

    import resend

    resend.api_key = settings.resend_api_key

    html = _render_email(team_name, stats)

    try:
        resend.Emails.send(
            {
                "from": f"AB-AI <{settings.email_from}>",
                "to": [to],
                "subject": f"Еженедельный отчёт — {team_name}",
                "html": html,
            }
        )
    except Exception:
        logger.exception("Failed to send weekly report to %s", to)


async def send_weekly_report_for_team(team_id: uuid.UUID) -> None:
    async with AsyncSessionFactory() as session:
        team = await session.scalar(select(Team).where(Team.id == team_id))
        if not team:
            return

        owner = await session.scalar(
            select(User).where(User.team_id == team_id, User.role == "owner")
        )
        if not owner:
            return

        stats = await _get_weekly_stats(team_id, session)
        await _send_email(owner.email, team.name, stats)


async def send_all_weekly_reports() -> None:
    async with AsyncSessionFactory() as session:
        teams = (await session.execute(select(Team))).scalars().all()
        for team in teams:
            try:
                await send_weekly_report_for_team(team.id)
            except Exception:
                logger.exception("Weekly report failed for team %s", team.id)
