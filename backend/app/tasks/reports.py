"""Celery task for weekly email reports."""

from __future__ import annotations

import asyncio
import logging

from app.services.report_service import send_all_weekly_reports
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.reports.weekly_report")
def weekly_report_task() -> None:
    try:
        asyncio.run(send_all_weekly_reports())
    except Exception:
        logger.exception("weekly_report_task crashed")
    finally:
        try:
            asyncio.run(_dispose_engine())
        except Exception:
            pass


async def _dispose_engine() -> None:
    from app.db.session import engine
    await engine.dispose()
