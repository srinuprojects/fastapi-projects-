import time
import random
import logging
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.send_email",
    max_retries=3,
    default_retry_delay=10,
    soft_time_limit=60,
)
def send_email(self, payload: dict) -> dict:
    """
    Simulate sending an email.
    Retries up to 3 times on failure with exponential backoff.
    """
    try:
        logger.info(f"Sending email to {payload['to']}")
        # Simulate occasional transient failures
        if random.random() < 0.2:
            raise ConnectionError("SMTP connection failed (simulated)")

        time.sleep(2)  # Simulate network latency

        return {
            "status": "sent",
            "to": payload["to"],
            "subject": payload["subject"],
            "message_id": f"msg-{self.request.id[:8]}",
        }

    except SoftTimeLimitExceeded:
        logger.error("Email task timed out")
        raise

    except Exception as exc:
        logger.warning(f"Email failed, retrying... ({self.request.retries}/3)")
        # Exponential backoff: 10s, 20s, 40s
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))


@celery_app.task(
    bind=True,
    name="app.workers.tasks.process_image",
    max_retries=2,
    soft_time_limit=120,
)
def process_image(self, payload: dict) -> dict:
    """
    Simulate image resizing/processing.
    """
    try:
        logger.info(f"Processing image: {payload['filename']}")
        time.sleep(5)  # Simulate heavy processing

        sizes = ["thumbnail_150x150", "medium_800x600", "large_1920x1080"]
        return {
            "status": "processed",
            "original": payload["filename"],
            "variants": sizes,
            "size_bytes": random.randint(50_000, 500_000),
        }

    except SoftTimeLimitExceeded:
        logger.error("Image processing timed out")
        raise

    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.generate_report",
    max_retries=1,
    soft_time_limit=180,
)
def generate_report(self, payload: dict) -> dict:
    """
    Simulate generating a CSV/PDF report.
    Also triggered by Celery Beat on a schedule.
    """
    try:
        logger.info(f"Generating report: {payload.get('type', 'custom')}")
        time.sleep(3)

        row_count = random.randint(100, 10_000)
        return {
            "status": "complete",
            "report_type": payload.get("type", "custom"),
            "rows": row_count,
            "download_url": f"/reports/{self.request.id}.csv",
        }

    except SoftTimeLimitExceeded:
        logger.error("Report generation timed out")
        raise

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
