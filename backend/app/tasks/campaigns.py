"""Celery tasks for campaign execution.

evaluate_triggers: runs every 15 minutes, picks up running campaigns
and dispatches them for execution.
"""

from __future__ import annotations

import asyncio
import logging

from app.db.session import AsyncSessionFactory
from app.services.campaign_engine import execute_campaign
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.campaigns.evaluate_triggers")
def evaluate_triggers() -> None:
    """Find all running campaigns and execute them."""
    from sqlalchemy import select
    from app.db.models.campaign import Campaign

    async def _run() -> None:
        async with AsyncSessionFactory() as session:
            rows = await session.scalars(
                select(Campaign).where(Campaign.status == "running")
            )
            running = rows.all()
            for campaign in running:
                try:
                    result = await execute_campaign(campaign.id)
                    logger.info(
                        "Campaign %s (%s): sent=%d, skipped=%d",
                        campaign.id,
                        campaign.name,
                        result.get("sent", 0),
                        result.get("skipped", 0),
                    )
                except Exception:
                    logger.exception("Campaign %s execution failed", campaign.id)

    try:
        asyncio.run(_run())
    except Exception:
        logger.exception("evaluate_triggers crashed")
    finally:
        try:
            asyncio.run(_dispose_engine())
        except Exception:
            pass


async def _dispose_engine() -> None:
    from app.db.session import engine
    await engine.dispose()