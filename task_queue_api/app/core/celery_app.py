from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "task_queue",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
    # Celery Beat: scheduled jobs
    beat_schedule={
        "send-daily-report": {
            "task": "app.workers.tasks.generate_report",
            "schedule": crontab(hour=8, minute=0),
            "args": ({"type": "daily_summary"},),
        },
    },
)
