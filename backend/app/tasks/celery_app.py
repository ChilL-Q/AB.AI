from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "ab_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.messages",
        "app.tasks.outreach",
        "app.tasks.reports",
        "app.tasks.campaigns",
        "app.tasks.feedback",
        "app.tasks.billing",
        "app.tasks.sync",
        "app.tasks.maintenance",
        "app.tasks.notifications",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "run-outreach-cycle-every-hour": {
        "task": "app.tasks.outreach.run_outreach_cycle",
        "schedule": crontab(minute=0),
    },
    "check-escalations-every-hour": {
        "task": "app.tasks.outreach.check_escalations",
        "schedule": crontab(minute=30),
    },
    "evaluate-campaign-triggers": {
        "task": "app.tasks.campaigns.evaluate_triggers",
        "schedule": crontab(minute="*/15"),
    },
    "run-feedback-loop-every-6-hours": {
        "task": "app.tasks.feedback.run_feedback_loop",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "generate-weekly-reports": {
        "task": "app.tasks.reports.weekly_report",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },
}
