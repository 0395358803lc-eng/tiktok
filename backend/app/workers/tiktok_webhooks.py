import logging
import time
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.models.tiktok_webhook_event import TikTokWebhookEvent
from app.services.tiktok.webhooks import process_webhook_event

configure_logging()
logger = logging.getLogger("tiktok-webhook-worker")

MAX_ATTEMPTS = 5


def run_once() -> tuple[int, int]:
    processed = 0
    failed = 0

    with SessionLocal() as db:
        rows = db.scalars(
            select(TikTokWebhookEvent)
            .where(
                TikTokWebhookEvent.status == "PENDING",
                TikTokWebhookEvent.attempts < MAX_ATTEMPTS,
            )
            .order_by(TikTokWebhookEvent.id.asc())
            .limit(100)
        ).all()

        for row in rows:
            row_id = row.id
            row.attempts += 1
            db.commit()

            try:
                result = process_webhook_event(db, row)
                current = db.get(TikTokWebhookEvent, row_id)
                if current is None:
                    continue
                current.status = result
                current.error_detail = None
                current.processed_at = datetime.now(UTC)
                db.commit()
                processed += 1
            except Exception as exc:
                db.rollback()
                current = db.get(TikTokWebhookEvent, row_id)
                if current is None:
                    continue
                current.error_detail = f"{type(exc).__name__}: {str(exc)[:800]}"
                if current.attempts >= MAX_ATTEMPTS:
                    current.status = "ERROR"
                    current.processed_at = datetime.now(UTC)
                else:
                    current.status = "PENDING"
                db.commit()
                failed += 1
                logger.exception(
                    "Webhook processing failed event_id=%s attempt=%s",
                    row_id,
                    current.attempts,
                )

    return processed, failed


def main() -> None:
    settings = get_settings()
    interval = max(settings.webhook_worker_interval_seconds, 2)
    logger.info("TikTok webhook worker started interval=%ss", interval)

    while True:
        try:
            processed, failed = run_once()
            logger.info(
                "Webhook cycle complete processed=%s failed=%s",
                processed,
                failed,
            )
        except Exception:
            logger.exception("Unexpected TikTok webhook worker error")
        time.sleep(interval)


if __name__ == "__main__":
    main()
