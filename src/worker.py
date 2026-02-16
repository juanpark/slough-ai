"""Celery app instance."""

from celery import Celery
from celery.schedules import crontab

from src.config import settings

celery_app = Celery(
    "slough",
    broker=settings.redis_broker_url,
    backend=settings.redis_backend_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    beat_schedule={
        "weekly-report-monday-10am": {
            "task": "send_weekly_reports",
            "schedule": crontab(hour=10, minute=0, day_of_week=1),
        },
        # 5분마다 미반영 피드백을 Knowledge Base에 동기화
        "sync-feedback-to-kb-every-5-minutes": {
            "task": "sync_feedback_to_kb",
            "schedule": 300.0,
        },
        # 매일 자정에 DB 규칙 → Redis 캐시 갱신
        "sync-rules-from-db-daily": {
            "task": "sync_rules_from_db",
            "schedule": crontab(hour=0, minute=0),
        },
    },
)

celery_app.conf.include = [
    "src.tasks.ingestion",
    "src.tasks.weekly_report",
    "src.tasks.feedback_sync",
]
