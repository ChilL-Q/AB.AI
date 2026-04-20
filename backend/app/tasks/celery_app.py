from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "ab_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.messages",
        "app.tasks.campaigns",
        "app.tasks.sync",
        "app.tasks.reports",
        "app.tasks.notifications",
        "app.tasks.billing",
        "app.tasks.maintenance",
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
    "evaluate-triggers-every-15min": {
        "task": "app.tasks.campaigns.evaluate_triggers",
        "schedule": crontab(minute="*/15"),
    },
    "update-segments-every-hour": {
        "task": "app.tasks.maintenance.update_segments",
        "schedule": crontab(minute=0),
    },
    "generate-weekly-reports": {
        "task": "app.tasks.reports.generate_report",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },
    "cleanup-soft-deleted": {
        "task": "app.tasks.maintenance.cleanup_soft_deleted",
        "schedule": crontab(hour=3, minute=0),
    },
}
