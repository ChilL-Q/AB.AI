from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.deps import CurrentUserDep, SessionDep
from app.core.exceptions import ForbiddenError
from app.db.models.client import Client
from app.db.models.conversation import Conversation
from app.db.models.outreach_attempt import OutreachAttempt
from app.db.models.visit import Visit

router = APIRouter()


def _team_id(current_user) -> UUID:
    if current_user.team_id is None:
        raise ForbiddenError("User has no team")
    return current_user.team_id


@router.get("/dashboard")
async def dashboard_stats(current_user: CurrentUserDep, session: SessionDep):
    tid = _team_id(current_user)

    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    active_clients = (
        await session.scalar(
            select(func.count()).select_from(
                select(Client).where(Client.team_id == tid, Client.deleted_at.is_(None)).subquery()
            )
        )
        or 0
    )

    today_start = now.replace(hour=0, minute=0, second=0)
    conversations_today = (
        await session.scalar(
            select(func.count()).select_from(
                select(Conversation)
                .where(Conversation.team_id == tid, Conversation.created_at >= today_start)
                .subquery()
            )
        )
        or 0
    )

    total_cars = (
        await session.scalar(
            select(func.count()).select_from(
                select(Visit.car_id)
                .where(Visit.team_id == tid, Visit.car_id.isnot(None))
                .subquery()
            )
        )
        or 0
    )

    retention_base = (
        await session.scalar(
            select(func.count()).select_from(
                select(Client)
                .where(
                    Client.team_id == tid,
                    Client.deleted_at.is_(None),
                    Client.total_visits >= 2,
                )
                .subquery()
            )
        )
        or 0
    )

    total_with_visits = (
        await session.scalar(
            select(func.count()).select_from(
                select(Client)
                .where(
                    Client.team_id == tid,
                    Client.deleted_at.is_(None),
                    Client.total_visits >= 1,
                )
                .subquery()
            )
        )
        or 1
    )

    retention_rate = round(retention_base / total_with_visits, 3) if total_with_visits else 0

    week_revenue = await session.scalar(
        select(func.coalesce(func.sum(Visit.total_amount), 0)).where(
            Visit.team_id == tid,
            Visit.visited_at >= week_ago,
        )
    ) or Decimal("0")

    prev_week_revenue = await session.scalar(
        select(func.coalesce(func.sum(Visit.total_amount), 0)).where(
            Visit.team_id == tid,
            Visit.visited_at >= two_weeks_ago,
            Visit.visited_at < week_ago,
        )
    ) or Decimal("0")

    revenue_delta = 0
    if prev_week_revenue and prev_week_revenue > 0:
        revenue_delta = round(
            float((week_revenue - prev_week_revenue) / prev_week_revenue * 100),
            1,
        )

    outreach_metrics = (
        await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt)
                .where(OutreachAttempt.team_id == tid, OutreachAttempt.resulted_in_visit.is_(True))
                .subquery()
            )
        )
        or 0
    )
    total_outreach = (
        await session.scalar(
            select(func.count()).select_from(
                select(OutreachAttempt).where(OutreachAttempt.team_id == tid).subquery()
            )
        )
        or 0
    )

    outreach_revenue = await session.scalar(
        select(func.coalesce(func.sum(OutreachAttempt.resulted_in_revenue), 0)).where(
            OutreachAttempt.team_id == tid
        )
    ) or Decimal("0")

    daily_rows = (
        await session.execute(
            select(
                func.to_char(Visit.visited_at, "Dy").label("d"),
                func.coalesce(func.sum(Visit.total_amount), 0).label("revenue"),
                func.count().label("visits"),
            )
            .where(Visit.team_id == tid, Visit.visited_at >= week_ago)
            .group_by(func.to_char(Visit.visited_at, "Dy"), Visit.visited_at.date())
            .order_by(Visit.visited_at.date())
        )
    ).all()

    chart = [{"d": r[0], "revenue": float(r[1]) / 1000, "visits": r[2]} for r in daily_rows]

    recent_outreach = (
        (
            await session.execute(
                select(OutreachAttempt)
                .where(OutreachAttempt.team_id == tid)
                .order_by(OutreachAttempt.created_at.desc())
                .limit(5)
            )
        )
        .scalars()
        .all()
    )

    recent_visits = (
        (
            await session.execute(
                select(Visit).where(Visit.team_id == tid).order_by(Visit.created_at.desc()).limit(3)
            )
        )
        .scalars()
        .all()
    )

    recent_clients = (
        (
            await session.execute(
                select(Client)
                .where(Client.team_id == tid, Client.deleted_at.is_(None))
                .order_by(Client.created_at.desc())
                .limit(2)
            )
        )
        .scalars()
        .all()
    )

    activity: list[dict] = []

    for a in recent_outreach:
        client_name = "Клиент"
        cl = await session.scalar(select(Client).where(Client.id == a.client_id))
        if cl:
            client_name = cl.full_name
        activity.append(
            {
                "type": "outreach",
                "title": f"AI написал {client_name}",
                "meta": (
                    (a.message_text or "")[:60]
                    + ("..." if a.message_text and len(a.message_text) > 60 else "")
                ),
                "time": a.created_at.isoformat() if a.created_at else "",
            }
        )

    for v in recent_visits:
        activity.append(
            {
                "type": "visit",
                "title": "Визит закрыт",
                "meta": f"₸{float(v.total_amount):,.0f}",
                "time": v.created_at.isoformat() if v.created_at else "",
            }
        )

    for c in recent_clients:
        activity.append(
            {
                "type": "client",
                "title": f"Новый клиент: {c.full_name}",
                "meta": f"Источник: {c.source or 'ручной'}",
                "time": c.created_at.isoformat() if c.created_at else "",
            }
        )

    activity.sort(key=lambda x: x["time"], reverse=True)
    activity = activity[:8]

    return {
        "active_clients": active_clients,
        "conversations_today": conversations_today,
        "total_cars": total_cars or 0,
        "retention_rate": retention_rate,
        "revenue_week": float(week_revenue),
        "revenue_delta": revenue_delta,
        "outreach_returned": outreach_metrics,
        "outreach_total": total_outreach,
        "outreach_revenue": float(outreach_revenue),
        "chart": chart,
        "activity": activity,
    }
