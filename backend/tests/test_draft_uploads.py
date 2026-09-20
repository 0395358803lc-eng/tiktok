from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.media_asset import MediaAsset
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_draft_job import TikTokDraftJob
from app.services.media_library import media_root
from app.services.tiktok.crypto import encrypt_token
from app.services.tiktok.drafts import (
    DraftInitResult,
    DraftStatusResult,
    TikTokDraftValidationError,
    validate_photo_request,
    video_chunk_plan,
)
from app.workers.tiktok_drafts import run_once


def _account(db) -> TikTokAccount:
    now = datetime.now(UTC)
    account = TikTokAccount(
        open_id="draft-test-open-id",
        scopes="user.info.basic,video.upload",
        access_token_enc=encrypt_token("draft-access"),
        refresh_token_enc=encrypt_token("draft-refresh"),
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


def test_video_chunk_plan_matches_tiktok_rules():
    one_mb = 1024 * 1024
    assert video_chunk_plan(4 * one_mb) == (4 * one_mb, 1)
    assert video_chunk_plan(64 * one_mb) == (64 * one_mb, 1)
    assert video_chunk_plan(70 * one_mb) == (64 * one_mb, 1)
    assert video_chunk_plan(140 * one_mb) == (64 * one_mb, 2)


def test_photo_validation():
    validate_photo_request(
        photo_urls=["https://example.com/a.jpg", "https://example.com/b.webp"],
        cover_index=1,
        title="Photos",
        description="Draft",
    )

    with pytest.raises(TikTokDraftValidationError):
        validate_photo_request(
            photo_urls=["http://example.com/a.jpg"],
            cover_index=0,
            title=None,
            description=None,
        )

    with pytest.raises(TikTokDraftValidationError):
        validate_photo_request(
            photo_urls=["https://example.com/a.jpg"] * 36,
            cover_index=0,
            title=None,
            description=None,
        )


def test_draft_worker_submits_and_polls_video(monkeypatch):
    now = datetime.now(UTC)
    stored_name = "draft-test-video.mp4"
    target = media_root() / stored_name
    target.write_bytes(b"video-test-bytes")
    target.chmod(0o600)

    with SessionLocal() as db:
        db.execute(
            delete(TikTokAccount).where(
                TikTokAccount.open_id == "draft-test-open-id"
            )
        )
        db.commit()
        account = _account(db)
        asset = MediaAsset(
            kind="VIDEO",
            original_name="test.mp4",
            stored_name=stored_name,
            mime_type="video/mp4",
            size_bytes=target.stat().st_size,
            sha256="0" * 64,
            created_at=now,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        job = TikTokDraftJob(
            account_id=account.id,
            media_asset_id=asset.id,
            media_type="VIDEO",
            source_type="FILE_UPLOAD",
            status="QUEUED",
            created_at=now,
            updated_at=now,
        )
        db.add(job)
        db.commit()
        job_id = job.id

    monkeypatch.setattr(
        "app.workers.tiktok_drafts.init_video_draft",
        lambda *_args, **_kwargs: DraftInitResult(
            publish_id="draft-publish-123",
            upload_url="https://upload.tiktokapis.com/video/test",
        ),
    )
    monkeypatch.setattr(
        "app.workers.tiktok_drafts.upload_video_file",
        lambda asset, _url: asset.size_bytes,
    )
    monkeypatch.setattr(
        "app.workers.tiktok_drafts.fetch_draft_status",
        lambda *_args, **_kwargs: DraftStatusResult(
            status="SEND_TO_USER_INBOX",
            fail_reason=None,
            uploaded_bytes=16,
            downloaded_bytes=None,
            public_post_ids=[],
        ),
    )

    submitted, polled = run_once()
    assert submitted >= 1
    assert polled >= 1

    with SessionLocal() as db:
        job = db.get(TikTokDraftJob, job_id)
        assert job is not None
        assert job.publish_id == "draft-publish-123"
        assert job.status == "SEND_TO_USER_INBOX"

        db.execute(delete(TikTokDraftJob).where(TikTokDraftJob.id == job_id))
        db.execute(delete(MediaAsset).where(MediaAsset.stored_name == stored_name))
        db.execute(
            delete(TikTokAccount).where(
                TikTokAccount.open_id == "draft-test-open-id"
            )
        )
        db.commit()

    target.unlink(missing_ok=True)
