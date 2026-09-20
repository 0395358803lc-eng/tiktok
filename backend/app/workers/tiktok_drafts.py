import json
import logging
import time
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select

from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.models.media_asset import MediaAsset
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_draft_job import TikTokDraftJob
from app.services.audit import record_audit
from app.services.tiktok.client import TikTokAPIError
from app.services.tiktok.drafts import (
    TikTokDraftScopeError,
    TikTokDraftValidationError,
    decode_photo_source,
    fetch_draft_status,
    init_photo_draft,
    init_video_draft,
    upload_video_file,
)

configure_logging()
logger = logging.getLogger("tiktok-draft-worker")

TERMINAL_STATUSES = {"PUBLISH_COMPLETE", "FAILED"}
INBOX_POLL_INTERVAL = timedelta(minutes=15)


def _fail_job(db, job: TikTokDraftJob, reason: str) -> None:
    job.status = "FAILED"
    job.fail_reason = reason[:1000]
    job.updated_at = datetime.now(UTC)
    db.commit()
    record_audit(
        db,
        event_type="DRAFT_FAILED",
        account_id=job.account_id,
        status="ERROR",
        detail=f"Draft job id={job.id} failed: {reason[:300]}",
    )


def _submit_job(db, job: TikTokDraftJob) -> bool:
    account = db.get(TikTokAccount, job.account_id)
    if account is None or account.status != "CONNECTED":
        _fail_job(db, job, "TikTok account is not connected")
        return False

    try:
        if job.media_type == "VIDEO":
            asset = db.get(MediaAsset, job.media_asset_id) if job.media_asset_id else None
            if asset is None:
                raise TikTokDraftValidationError("Video media asset is missing")

            job.status = "INITIALIZING"
            job.updated_at = datetime.now(UTC)
            db.commit()

            init = init_video_draft(account, asset)
            job.publish_id = init.publish_id
            job.status = "UPLOADING"
            job.updated_at = datetime.now(UTC)
            db.commit()

            if not init.upload_url:
                raise TikTokAPIError("TikTok upload URL is missing")
            uploaded = upload_video_file(asset, init.upload_url)
            job.uploaded_bytes = uploaded
            job.status = "SUBMITTED"
            job.updated_at = datetime.now(UTC)
            db.commit()

        elif job.media_type == "PHOTO":
            urls, cover_index, is_aigc = decode_photo_source(job.source_json)
            job.status = "INITIALIZING"
            job.updated_at = datetime.now(UTC)
            db.commit()
            init = init_photo_draft(
                account,
                photo_urls=urls,
                cover_index=cover_index,
                title=job.title,
                description=job.description,
                is_aigc=is_aigc,
            )
            job.publish_id = init.publish_id
            job.status = "SUBMITTED"
            job.updated_at = datetime.now(UTC)
            db.commit()
        else:
            raise TikTokDraftValidationError("Unsupported draft media type")

        record_audit(
            db,
            event_type="DRAFT_SUBMITTED",
            account_id=job.account_id,
            detail=f"Draft job id={job.id} submitted to TikTok",
        )
        logger.info(
            "Draft submitted job_id=%s account_id=%s media_type=%s",
            job.id,
            job.account_id,
            job.media_type,
        )
        return True
    except (
        TikTokDraftScopeError,
        TikTokDraftValidationError,
        TikTokAPIError,
        httpx.RequestError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        _fail_job(db, job, str(exc))
        logger.warning(
            "Draft submission failed job_id=%s error=%s",
            job.id,
            type(exc).__name__,
        )
        return False


def _poll_job(db, job: TikTokDraftJob) -> bool:
    if not job.publish_id or job.status in TERMINAL_STATUSES:
        return False

    now = datetime.now(UTC)
    if (
        job.status == "SEND_TO_USER_INBOX"
        and now - job.updated_at < INBOX_POLL_INTERVAL
    ):
        return False

    account = db.get(TikTokAccount, job.account_id)
    if account is None or account.status != "CONNECTED":
        return False

    try:
        remote = fetch_draft_status(account, job.publish_id)
    except (TikTokDraftScopeError, TikTokAPIError, httpx.RequestError) as exc:
        logger.warning(
            "Draft status fetch failed job_id=%s error=%s",
            job.id,
            type(exc).__name__,
        )
        return False

    previous = job.status
    job.status = remote.status
    job.fail_reason = remote.fail_reason
    job.uploaded_bytes = remote.uploaded_bytes or job.uploaded_bytes
    job.downloaded_bytes = remote.downloaded_bytes
    job.public_post_ids = json.dumps(remote.public_post_ids)
    job.updated_at = now
    db.commit()

    if previous != job.status:
        event = {
            "SEND_TO_USER_INBOX": "DRAFT_INBOX_DELIVERED",
            "PUBLISH_COMPLETE": "DRAFT_PUBLISH_COMPLETE",
            "FAILED": "DRAFT_FAILED",
        }.get(job.status, "DRAFT_STATUS_CHANGED")
        record_audit(
            db,
            event_type=event,
            account_id=job.account_id,
            status=("ERROR" if job.status == "FAILED" else "SUCCESS"),
            detail=f"Draft job id={job.id} status={job.status}",
        )
    return True


def run_once() -> tuple[int, int]:
    submitted = 0
    polled = 0
    with SessionLocal() as db:
        queued = db.scalars(
            select(TikTokDraftJob)
            .where(TikTokDraftJob.status == "QUEUED")
            .order_by(TikTokDraftJob.id.asc())
            .limit(5)
        ).all()
        for job in queued:
            if _submit_job(db, job):
                submitted += 1

        active = db.scalars(
            select(TikTokDraftJob)
            .where(
                TikTokDraftJob.publish_id.is_not(None),
                TikTokDraftJob.status.not_in(TERMINAL_STATUSES),
            )
            .order_by(TikTokDraftJob.id.asc())
            .limit(50)
        ).all()
        for job in active:
            if _poll_job(db, job):
                polled += 1

    return submitted, polled


def main() -> None:
    settings = get_settings()
    interval = max(settings.draft_worker_interval_seconds, 15)
    logger.info("TikTok draft worker started interval=%ss", interval)
    while True:
        try:
            submitted, polled = run_once()
            logger.info(
                "Draft cycle complete submitted=%s polled=%s",
                submitted,
                polled,
            )
        except Exception:
            logger.exception("Unexpected TikTok draft worker error")
        time.sleep(interval)


if __name__ == "__main__":
    main()
