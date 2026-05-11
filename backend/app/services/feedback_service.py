"""Feedback loop — correlate visits with outreach attempts.

For each outreach attempt that was "sent" or "replied", check if the client
had a visit AFTER the outreach was sent. If yes, mark `resulted_in_visit`
and set `resulted_in_revenue` to the visit's total_amount.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.outreach_attempt import OutreachAttempt
from app.db.models.visit import Visit

logger = logging.getLogger(__name__)

ATTRIBUTION_WINDOW_DAYS = 30


async def attribute_visits(session: AsyncSession, team_id: uuid.UUID | None = None) -> int:
    """Find outreach attempts where the client visited after being contacted.

    Updates `resulted_in_visit` and `resulted_in_revenue` on matching attempts.
    Returns the number of attempts updated.
    """
    from datetime import UTC, datetime, timedelta

    window_start = datetime.now(UTC) - timedelta(days=ATTRIBUTION_WINDOW_DAYS)

    query = select(OutreachAttempt).where(
        OutreachAttempt.resulted_in_visit.is_(False),
        OutreachAttempt.status.in_(["sent", "replied"]),
        OutreachAttempt.sent_at.isnot(None),
        OutreachAttempt.sent_at >= window_start,
    )
    if team_id:
        query = query.where(OutreachAttempt.team_id == team_id)

    rows = await session.execute(query)
    attempts = rows.scalars().all()

    updated = 0
    for attempt in attempts:
        visit = await session.scalar(
            select(Visit).where(
                Visit.client_id == attempt.client_id,
                Visit.team_id == attempt.team_id,
                Visit.visited_at > attempt.sent_at,
            ).order_by(Visit.visited_at.asc()).limit(1)
        )
        if visit:
            attempt.resulted_in_visit = True
            attempt.resulted_in_revenue = visit.total_amount
            updated += 1

    if updated:
        await session.flush()

    return updated