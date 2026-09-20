import logging
import time
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select

from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.models.tiktok_publish_job import TikTokPublishJob
from app.services.audit import record_audit

configure_logging()
logger = logging.getLogger("tiktok-scheduler-worker")


def run_once() -> int:
    settings = get_settings()
    now = datetime.now(UTC)
    promoted = 0

    with SessionLocal() as db:
        rows = db.scalars(
            select(TikTokPublishJob)
            .where(
                TikTokPublishJob.status == "QUEUED",
                TikTokPublishJob.schedule_status == "SCHEDULED",
                or_(
                    and_(
                        TikTokPublishJob.next_attempt_at.is_not(None),
                        TikTokPublishJob.next_attempt_at <= now,
                    ),
                    and_(
                        TikTokPublishJob.next_attempt_at.is_(None),
                        TikTokPublishJob.scheduled_at.is_not(None),
                        TikTokPublishJob.scheduled_at <= now,
                    ),
                ),
            )
            .order_by(
                TikTokPublishJob.next_attempt_at.asc().nulls_last(),
                TikTokPublishJob.scheduled_at.asc().nulls_last(),
                TikTokPublishJob.id.asc(),
            )
            .limit(settings.scheduler_ready_batch_size)
        ).all()

        for job in rows:
            job.schedule_status = "READY"
            job.updated_at = now
            db.commit()
            record_audit(
                db,
                event_type="DIRECT_POST_READY",
                account_id=job.account_id,
                detail=f"Scheduled Direct Post job id={job.id} is ready",
            )
            promoted += 1

    return promoted


def main() -> None:
    settings = get_settings()
    interval = max(settings.scheduler_worker_interval_seconds, 2)
    logger.info(
        "TikTok scheduler worker started interval=%ss batch=%s",
        interval,
        settings.scheduler_ready_batch_size,
    )
    while True:
        try:
            promoted = run_once()
            logger.info("Scheduler cycle complete promoted=%s", promoted)
        except Exception:
            logger.exception("Unexpected TikTok scheduler worker error")
        time.sleep(interval)


if __name__ == "__main__":
    main()
