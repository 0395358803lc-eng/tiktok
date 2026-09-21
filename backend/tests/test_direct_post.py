from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.media_asset import MediaAsset
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_publish_job import TikTokPublishJob
from app.services.media_library import media_root
from app.services.tiktok.client import TikTokAPIError
from app.services.tiktok.crypto import encrypt_token
from app.services.tiktok.direct_posts import (
    CreatorInfo,
    DirectPostOptions,
    TikTokPublishValidationError,
    _payload,
    validate_direct_post,
)
from app.services.tiktok.drafts import DraftInitResult, DraftStatusResult
from app.workers.tiktok_publish import run_once


def _creator_info() -> CreatorInfo:
    return CreatorInfo(
        creator_avatar_url=None,
        creator_username="creator",
        creator_nickname="Creator",
        privacy_level_options=[
            "PUBLIC_TO_EVERYONE",
            "MUTUAL_FOLLOW_FRIENDS",
            "SELF_ONLY",
        ],
        comment_disabled=False,
        duet_disabled=False,
        stitch_disabled=False,
        max_video_post_duration_sec=60,
    )


def _options(**overrides) -> DirectPostOptions:
    values = {
        "privacy_level": "PUBLIC_TO_EVERYONE",
        "allow_comment": False,
        "allow_duet": False,
        "allow_stitch": False,
        "brand_content_toggle": False,
        "brand_organic_toggle": False,
        "is_aigc": False,
        "consent_music_usage": True,
        "consent_branded_policy": False,
        "title": "Test post",
    }
    values.update(overrides)
    return DirectPostOptions(**values)


def test_unaudited_private_account_error_is_actionable():
    response = httpx.Response(
        403,
        json={
            "data": {},
            "error": {
                "code": "unaudited_client_can_only_post_to_private_accounts",
                "message": "Please review our integration guidelines",
                "log_id": "test-log-id",
            },
        },
    )

    with pytest.raises(TikTokAPIError) as exc_info:
        _payload(response, "Direct Post video initialization")

    message = str(exc_info.value)
    assert "Riêng tư (Private)" in message
    assert "SELF_ONLY" in message
    assert "code=unaudited_client_can_only_post_to_private_accounts" in message
    assert "log_id=test-log-id" in message


def _account(db) -> TikTokAccount:
    now = datetime.now(UTC)
    account = TikTokAccount(
        open_id="publish-test-open-id",
        scopes="user.info.basic,video.publish",
        access_token_enc=encrypt_token("publish-access"),
        refresh_token_enc=encrypt_token("publish-refresh"),
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


def test_direct_post_validation_requires_current_creator_options_and_consent():
    asset = MediaAsset(
        kind="VIDEO",
        original_name="test.mp4",
        stored_name="unused.mp4",
        mime_type="video/mp4",
        size_bytes=1024,
        sha256="0" * 64,
        duration_seconds=30,
        created_at=datetime.now(UTC),
    )

    with pytest.raises(TikTokPublishValidationError):
        validate_direct_post(
            info=_creator_info(),
            media_type="VIDEO",
            options=_options(privacy_level="FOLLOWER_OF_CREATOR"),
            asset=asset,
        )

    with pytest.raises(TikTokPublishValidationError):
        validate_direct_post(
            info=_creator_info(),
            media_type="VIDEO",
            options=_options(consent_music_usage=False),
            asset=asset,
        )


def test_direct_post_validation_commercial_and_duration_rules():
    short_asset = MediaAsset(
        kind="VIDEO",
        original_name="short.mp4",
        stored_name="short.mp4",
        mime_type="video/mp4",
        size_bytes=1024,
        sha256="1" * 64,
        duration_seconds=30,
        created_at=datetime.now(UTC),
    )
    long_asset = MediaAsset(
        kind="VIDEO",
        original_name="long.mp4",
        stored_name="long.mp4",
        mime_type="video/mp4",
        size_bytes=1024,
        sha256="2" * 64,
        duration_seconds=90,
        created_at=datetime.now(UTC),
    )

    with pytest.raises(TikTokPublishValidationError):
        validate_direct_post(
            info=_creator_info(),
            media_type="VIDEO",
            options=_options(
                privacy_level="SELF_ONLY",
                brand_content_toggle=True,
                consent_branded_policy=True,
            ),
            asset=short_asset,
        )

    with pytest.raises(TikTokPublishValidationError):
        validate_direct_post(
            info=_creator_info(),
            media_type="VIDEO",
            options=_options(),
            asset=long_asset,
        )


def test_direct_post_respects_interaction_disables():
    info = _creator_info()
    info.comment_disabled = True
    info.duet_disabled = True
    info.stitch_disabled = True
    asset = MediaAsset(
        kind="VIDEO",
        original_name="test.mp4",
        stored_name="unused.mp4",
        mime_type="video/mp4",
        size_bytes=1024,
        sha256="3" * 64,
        duration_seconds=10,
        created_at=datetime.now(UTC),
    )

    for key in ("allow_comment", "allow_duet", "allow_stitch"):
        with pytest.raises(TikTokPublishValidationError):
            validate_direct_post(
                info=info,
                media_type="VIDEO",
                options=_options(**{key: True}),
                asset=asset,
            )


def test_publish_worker_submits_and_polls_video(monkeypatch):
    now = datetime.now(UTC)
    stored_name = "publish-test-video.mp4"
    target = media_root() / stored_name
    target.write_bytes(b"publish-video-test")
    target.chmod(0o600)

    with SessionLocal() as db:
        db.execute(
            delete(TikTokAccount).where(
                TikTokAccount.open_id == "publish-test-open-id"
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
            sha256="4" * 64,
            duration_seconds=10,
            created_at=now,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        job = TikTokPublishJob(
            account_id=account.id,
            media_asset_id=asset.id,
            media_type="VIDEO",
            source_type="FILE_UPLOAD",
            title="Test",
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
            status="QUEUED",
            created_at=now,
            updated_at=now,
        )
        db.add(job)
        db.commit()
        job_id = job.id

    monkeypatch.setattr(
        "app.workers.tiktok_publish.query_creator_info",
        lambda *_args, **_kwargs: _creator_info(),
    )
    monkeypatch.setattr(
        "app.workers.tiktok_publish.init_video_direct_post",
        lambda *_args, **_kwargs: DraftInitResult(
            publish_id="publish-123",
            upload_url="https://upload.tiktokapis.com/video/test",
        ),
    )
    monkeypatch.setattr(
        "app.workers.tiktok_publish.upload_video_file",
        lambda asset, _url: asset.size_bytes,
    )
    monkeypatch.setattr(
        "app.workers.tiktok_publish.fetch_publish_status",
        lambda *_args, **_kwargs: DraftStatusResult(
            status="PUBLISH_COMPLETE",
            fail_reason=None,
            uploaded_bytes=18,
            downloaded_bytes=None,
            public_post_ids=["post-123"],
        ),
    )

    submitted, polled = run_once()
    assert submitted >= 1
    assert polled >= 1

    with SessionLocal() as db:
        job = db.get(TikTokPublishJob, job_id)
        assert job is not None
        assert job.publish_id == "publish-123"
        assert job.status == "PUBLISH_COMPLETE"
        assert "post-123" in (job.public_post_ids or "")

        db.execute(delete(TikTokPublishJob).where(TikTokPublishJob.id == job_id))
        db.execute(delete(MediaAsset).where(MediaAsset.stored_name == stored_name))
        db.execute(
            delete(TikTokAccount).where(
                TikTokAccount.open_id == "publish-test-open-id"
            )
        )
        db.commit()

    target.unlink(missing_ok=True)
