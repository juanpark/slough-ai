"""Celery app instance."""

from celery import Celery
from celery.schedules import crontab

from src.config import settings

celery_app = Celery(
    "slough",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "weekly-report-monday-10am": {
            "task": "send_weekly_reports",
            "schedule": crontab(hour=10, minute=0, day_of_week=1),  # Monday 10:00 AM KST
        },
    },
)

# Auto-discover tasks in src/tasks/
celery_app.autodiscover_tasks(["src.tasks"])
