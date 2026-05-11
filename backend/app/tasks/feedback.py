"""Celery task for the feedback loop — attribute visits to outreach attempts."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.db.models.team import Team
from app.db.session import AsyncSessionFactory
from app.services.feedback_service import attribute_visits
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_feedback_loop() -> None:
    async with AsyncSessionFactory() as session:
        teams = (await session.execute(select(Team))).scalars().all()
        total_updated = 0
        for team in teams:
            try:
                updated = await attribute_visits(session, team_id=team.id)
                total_updated += updated
            except Exception:
                logger.exception("Feedback loop failed for team %s", team.id)
        if total_updated:
            await session.commit()
        logger.info("Feedback loop: attributed %d visits to outreach", total_updated)


@celery_app.task(name="app.tasks.feedback.run_feedback_loop")
def run_feedback_loop_task() -> None:
    try:
        asyncio.run(_run_feedback_loop())
    except Exception:
        logger.exception("run_feedback_loop_task crashed")
    finally:
        try:
            asyncio.run(_dispose_engine())
        except Exception:
            pass


async def _dispose_engine() -> None:
    from app.db.session import engine
    await engine.dispose()