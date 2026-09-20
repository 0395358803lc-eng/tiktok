from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import delete

from app.api.publishing import (
    cancel_publish_job,
    reschedule_publish_job,
    retry_publish_job,
)
from app.db.session import SessionLocal
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_publish_job import TikTokPublishJob
from app.schemas.publishing import PublishRescheduleRequest
from app.services.tiktok.crypto import encrypt_token
from app.workers.tiktok_publish import _submit_job
from app.workers.tiktok_scheduler import run_once as run_scheduler_once


def _account(db, open_id: str) -> TikTokAccount:
    now = datetime.now(UTC)
    account = TikTokAccount(
        open_id=open_id,
        scopes="user.info.basic,video.publish",
        access_token_enc=encrypt_token("scheduler-access"),
        refresh_token_enc=encrypt_token("scheduler-refresh"),
        access_token_expires_at=now + timedelta(days=1),
        refresh_token_expires_at=now + timedelta(days=30),
        status="CONNECTED",
        created_at=now,
        updated_at=now,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def _job(
    db,
    account: TikTokAccount,
    *,
    schedule_status: str,
    status: str = "QUEUED",
    scheduled_at: datetime | None = None,
    retry_count: int = 0,
    max_retries: int = 2,
) -> TikTokPublishJob:
    now = datetime.now(UTC)
    job = TikTokPublishJob(
        account_id=account.id,
        media_type="PHOTO",
        source_type="PULL_FROM_URL",
        source_json='{"photo_urls":["https://example.com/a.jpg"],"cover_index":0}',
        title="Scheduled test",
        privacy_level="SELF_ONLY",
        disable_comment=True,
        disable_duet=True,
        disable_stitch=True,
        auto_add_music=False,
        brand_content_toggle=False,
        brand_organic_toggle=False,
        is_aigc=False,
        consent_music_usage=True,
        consent_branded_policy=False,
        creator_info_json="{}",
        status=status,
        scheduled_at=scheduled_at,
        schedule_status=schedule_status,
        retry_count=retry_count,
        max_retries=max_retries,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _cleanup(db, account_id: int) -> None:
    db.execute(
        delete(TikTokPublishJob).where(TikTokPublishJob.account_id == account_id)
    )
    db.execute(delete(TikTokAccount).where(TikTokAccount.id == account_id))
    db.commit()


def test_scheduler_promotes_due_job():
    with SessionLocal() as db:
        account = _account(db, "scheduler-due-open-id")
        job = _job(
            db,
            account,
            schedule_status="SCHEDULED",
            scheduled_at=datetime.now(UTC) - timedelta(seconds=5),
        )
        job_id = job.id
        account_id = account.id

    promoted = run_scheduler_once()
    assert promoted >= 1

    with SessionLocal() as db:
        job = db.get(TikTokPublishJob, job_id)
        assert job is not None
        assert job.schedule_status == "READY"
        assert job.status == "QUEUED"
        _cleanup(db, account_id)


def test_cancel_and_reschedule_pre_submit_job():
    with SessionLocal() as db:
        account = _account(db, "scheduler-cancel-open-id")
        original = datetime.now(UTC) + timedelta(hours=2)
        job = _job(
            db,
            account,
            schedule_status="SCHEDULED",
            scheduled_at=original,
        )
        account_id = account.id

        new_time = datetime.now(UTC) + timedelta(hours=4)
        summary = reschedule_publish_job(
            job.id,
            PublishRescheduleRequest(scheduled_at=new_time),
            None,
            db,
        )
        assert summary.schedule_status == "SCHEDULED"
        assert summary.scheduled_at is not None
        assert abs((summary.scheduled_at - new_time).total_seconds()) < 1

        canceled = cancel_publish_job(job.id, None, db)
        assert canceled.status == "CANCELED"
        assert canceled.schedule_status == "CANCELED"
        assert canceled.canceled_at is not None

        _cleanup(db, account_id)


def test_manual_retry_respects_limit():
    with SessionLocal() as db:
        account = _account(db, "scheduler-retry-open-id")
        job = _job(
            db,
            account,
            schedule_status="FAILED",
            status="FAILED",
            retry_count=0,
            max_retries=2,
        )
        account_id = account.id

        summary = retry_publish_job(job.id, None, db)
        assert summary.status == "QUEUED"
        assert summary.schedule_status == "READY"
        assert summary.retry_count == 1

        job.status = "FAILED"
        job.schedule_status = "FAILED"
        db.commit()
        summary = retry_publish_job(job.id, None, db)
        assert summary.retry_count == 2

        _cleanup(db, account_id)


def test_creator_info_network_failure_schedules_safe_retry(monkeypatch):
    with SessionLocal() as db:
        account = _account(db, "scheduler-network-open-id")
        job = _job(
            db,
            account,
            schedule_status="READY",
            retry_count=0,
            max_retries=2,
        )
        job_id = job.id
        account_id = account.id

        request = httpx.Request("POST", "https://open.tiktokapis.com")
        monkeypatch.setattr(
            "app.workers.tiktok_publish.query_creator_info",
            lambda _account: (_ for _ in ()).throw(
                httpx.ConnectError("temporary network failure", request=request)
            ),
        )

        submitted = _submit_job(db, job)
        assert submitted is False

    with SessionLocal() as db:
        job = db.get(TikTokPublishJob, job_id)
        assert job is not None
        assert job.publish_id is None
        assert job.status == "QUEUED"
        assert job.schedule_status == "SCHEDULED"
        assert job.retry_count == 1
        assert job.next_attempt_at is not None
        _cleanup(db, account_id)
