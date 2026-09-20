import json
import logging
import time
from datetime import UTC, datetime

import httpx
from sqlalchemy import select

from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.models.media_asset import MediaAsset
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_publish_job import TikTokPublishJob
from app.services.audit import record_audit
from app.services.tiktok.client import TikTokAPIError
from app.services.tiktok.direct_posts import (
    DirectPostOptions,
    TikTokPublishScopeError,
    TikTokPublishValidationError,
    fetch_publish_status,
    init_photo_direct_post,
    init_video_direct_post,
    query_creator_info,
    upload_video_file,
)

configure_logging()
logger = logging.getLogger("tiktok-publish-worker")

TERMINAL_STATUSES = {"PUBLISH_COMPLETE", "FAILED"}


def _options(job: TikTokPublishJob) -> DirectPostOptions:
    return DirectPostOptions(
        privacy_level=job.privacy_level,
        allow_comment=not job.disable_comment,
        allow_duet=not job.disable_duet,
        allow_stitch=not job.disable_stitch,
        brand_content_toggle=job.brand_content_toggle,
        brand_organic_toggle=job.brand_organic_toggle,
        is_aigc=job.is_aigc,
        consent_music_usage=job.consent_music_usage,
        consent_branded_policy=job.consent_branded_policy,
        title=job.title,
        description=job.description,
        auto_add_music=job.auto_add_music,
        video_cover_timestamp_ms=job.video_cover_timestamp_ms,
    )


def _fail_job(db, job: TikTokPublishJob, reason: str) -> None:
    job.status = "FAILED"
    job.fail_reason = reason[:1000]
    job.updated_at = datetime.now(UTC)
    db.commit()
    record_audit(
        db,
        event_type="DIRECT_POST_FAILED",
        account_id=job.account_id,
        status="ERROR",
        detail=f"Direct Post job id={job.id} failed: {reason[:300]}",
    )


def _submit_job(db, job: TikTokPublishJob) -> bool:
    account = db.get(TikTokAccount, job.account_id)
    if account is None or account.status != "CONNECTED":
        _fail_job(db, job, "TikTok account is not connected")
        return False

    try:
        info = query_creator_info(account)
        options = _options(job)
        job.creator_info_json = json.dumps(
            {
                "creator_avatar_url": info.creator_avatar_url,
                "creator_username": info.creator_username,
                "creator_nickname": info.creator_nickname,
                "privacy_level_options": info.privacy_level_options,
                "comment_disabled": info.comment_disabled,
                "duet_disabled": info.duet_disabled,
                "stitch_disabled": info.stitch_disabled,
                "max_video_post_duration_sec": info.max_video_post_duration_sec,
            },
            separators=(",", ":"),
        )
        job.status = "INITIALIZING"
        job.updated_at = datetime.now(UTC)
        db.commit()

        if job.media_type == "VIDEO":
            asset = db.get(MediaAsset, job.media_asset_id) if job.media_asset_id else None
            if asset is None:
                raise TikTokPublishValidationError("Video media asset is missing")
            init = init_video_direct_post(
                account,
                asset,
                info=info,
                options=options,
            )
            job.publish_id = init.publish_id
            job.status = "UPLOADING"
            job.updated_at = datetime.now(UTC)
            db.commit()

            if not init.upload_url:
                raise TikTokAPIError("TikTok Direct Post upload URL is missing")
            uploaded = upload_video_file(asset, init.upload_url)
            job.uploaded_bytes = uploaded
            job.status = "SUBMITTED"
            job.updated_at = datetime.now(UTC)
            db.commit()

        elif job.media_type == "PHOTO":
            if not job.source_json:
                raise TikTokPublishValidationError("Photo source is missing")
            source = json.loads(job.source_json)
            photo_urls = [str(value) for value in source.get("photo_urls") or []]
            cover_index = int(source.get("cover_index", 0))
            init = init_photo_direct_post(
                account,
                info=info,
                options=options,
                photo_urls=photo_urls,
                cover_index=cover_index,
            )
            job.publish_id = init.publish_id
            job.status = "SUBMITTED"
            job.updated_at = datetime.now(UTC)
            db.commit()
        else:
            raise TikTokPublishValidationError("Unsupported Direct Post media type")

        record_audit(
            db,
            event_type="DIRECT_POST_SUBMITTED",
            account_id=job.account_id,
            detail=f"Direct Post job id={job.id} submitted to TikTok",
        )
        logger.info(
            "Direct Post submitted job_id=%s account_id=%s media_type=%s",
            job.id,
            job.account_id,
            job.media_type,
        )
        return True
    except (
        TikTokPublishScopeError,
        TikTokPublishValidationError,
        TikTokAPIError,
        httpx.RequestError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        _fail_job(db, job, str(exc))
        logger.warning(
            "Direct Post submission failed job_id=%s error=%s",
            job.id,
            type(exc).__name__,
        )
        return False


def _poll_job(db, job: TikTokPublishJob) -> bool:
    if not job.publish_id or job.status in TERMINAL_STATUSES:
        return False

    account = db.get(TikTokAccount, job.account_id)
    if account is None or account.status != "CONNECTED":
        return False

    try:
        remote = fetch_publish_status(account, job.publish_id)
    except (TikTokPublishScopeError, TikTokAPIError, httpx.RequestError) as exc:
        logger.warning(
            "Direct Post status fetch failed job_id=%s error=%s",
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
    job.updated_at = datetime.now(UTC)
    db.commit()

    if previous != job.status:
        event = {
            "PUBLISH_COMPLETE": "DIRECT_POST_COMPLETE",
            "FAILED": "DIRECT_POST_FAILED",
        }.get(job.status, "DIRECT_POST_STATUS_CHANGED")
        record_audit(
            db,
            event_type=event,
            account_id=job.account_id,
            status=("ERROR" if job.status == "FAILED" else "SUCCESS"),
            detail=f"Direct Post job id={job.id} status={job.status}",
        )
    return True


def run_once() -> tuple[int, int]:
    submitted = 0
    polled = 0
    with SessionLocal() as db:
        queued = db.scalars(
            select(TikTokPublishJob)
            .where(TikTokPublishJob.status == "QUEUED")
            .order_by(TikTokPublishJob.id.asc())
            .limit(5)
        ).all()
        for job in queued:
            if _submit_job(db, job):
                submitted += 1

        active = db.scalars(
            select(TikTokPublishJob)
            .where(
                TikTokPublishJob.publish_id.is_not(None),
                TikTokPublishJob.status.not_in(TERMINAL_STATUSES),
            )
            .order_by(TikTokPublishJob.id.asc())
            .limit(50)
        ).all()
        for job in active:
            if _poll_job(db, job):
                polled += 1

    return submitted, polled


def main() -> None:
    settings = get_settings()
    interval = max(settings.publish_worker_interval_seconds, 15)
    logger.info("TikTok publish worker started interval=%ss", interval)
    while True:
        try:
            submitted, polled = run_once()
            logger.info(
                "Publish cycle complete submitted=%s polled=%s",
                submitted,
                polled,
            )
        except Exception:
            logger.exception("Unexpected TikTok publish worker error")
        time.sleep(interval)


if __name__ == "__main__":
    main()
