"""Celery tasks for proactive AI outreach.

Runs periodically to scan clients, ask the LLM who to contact,
and send personalized outreach messages.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.db.models.team import Team
from app.db.session import AsyncSessionFactory
from app.realtime.bus import publish_nowait
from app.realtime.events import RealtimeEvent
from app.services.outreach_service import check_and_escalate, run_outreach_cycle
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_outreach_for_all_teams() -> None:
    async with AsyncSessionFactory() as session:
        team_rows = await session.execute(select(Team))
        teams = team_rows.scalars().all()

        for team in teams:
            try:
                results = await run_outreach_cycle(team.id, session)
                for r in results:
                    publish_nowait(
                        RealtimeEvent(
                            type="message.new",
                            team_id=team.id,
                            conversation_id=None,
                            payload={
                                "outreach_id": str(r.id),
                                "client_name": r.client_name,
                                "message": r.message_text,
                                "status": r.status,
                            },
                        )
                    )
            except Exception:
                logger.exception("Outreach cycle failed for team %s", team.id)


async def _run_escalation_check() -> None:
    async with AsyncSessionFactory() as session:
        team_rows = await session.execute(select(Team))
        teams = team_rows.scalars().all()

        for team in teams:
            try:
                escalated = await check_and_escalate(team.id, session)
                if escalated:
                    await session.commit()
                    for client_id in escalated:
                        publish_nowait(
                            RealtimeEvent(
                                type="message.new",
                                team_id=team.id,
                                conversation_id=None,
                                payload={
                                    "escalation": True,
                                    "client_id": str(client_id),
                                    "message": (
                                        "Клиент не отвечает на 2 сообщения. "
                                        "Рекомендуется позвонить."
                                    ),
                                },
                            )
                        )
            except Exception:
                logger.exception("Escalation check failed for team %s", team.id)


async def _dispose_engine() -> None:
    from app.db.session import engine
    await engine.dispose()


@celery_app.task(name="app.tasks.outreach.run_outreach_cycle")
def run_outreach_cycle_task() -> None:
    try:
        asyncio.run(_run_outreach_for_all_teams())
    except Exception:
        logging.exception("run_outreach_cycle_task crashed")
    finally:
        try:
            asyncio.run(_dispose_engine())
        except Exception:
            pass


@celery_app.task(name="app.tasks.outreach.check_escalations")
def check_escalations_task() -> None:
    try:
        asyncio.run(_run_escalation_check())
    except Exception:
        logging.exception("check_escalations_task crashed")
    finally:
        try:
            asyncio.run(_dispose_engine())
        except Exception:
            pass
