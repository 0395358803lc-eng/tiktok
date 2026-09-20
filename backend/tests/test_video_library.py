from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_video import TikTokVideo
from app.services.tiktok.crypto import encrypt_token
from app.services.tiktok.videos import (
    TikTokVideoScopeError,
    VideoItem,
    VideoPage,
    sync_video_page,
)


def _make_account(db, *, open_id: str, scopes: str) -> TikTokAccount:
    now = datetime.now(UTC)
    account = TikTokAccount(
        open_id=open_id,
        scopes=scopes,
        access_token_enc=encrypt_token("video-access"),
        refresh_token_enc=encrypt_token("video-refresh"),
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


def test_video_sync_requires_video_list_scope():
    with SessionLocal() as db:
        account = _make_account(
            db,
            open_id="video-no-scope",
            scopes="user.info.basic",
        )
        with pytest.raises(TikTokVideoScopeError):
            sync_video_page(db, account)

        db.delete(account)
        db.commit()


def test_video_sync_upserts_metadata(monkeypatch):
    now = datetime.now(UTC)
    with SessionLocal() as db:
        account = _make_account(
            db,
            open_id="video-sync-open-id",
            scopes="user.info.basic,video.list",
        )

        page = VideoPage(
            videos=[
                VideoItem(
                    video_id="video-123",
                    create_time=now,
                    cover_image_url="https://example.com/cover.jpg",
                    share_url="https://www.tiktok.com/@user/video/123",
                    video_description="Description",
                    duration=12,
                    height=1920,
                    width=1080,
                    title="Video title",
                    embed_link="https://www.tiktok.com/player/v1/123",
                    like_count=10,
                    comment_count=2,
                    share_count=3,
                    view_count=100,
                    is_aigc=False,
                )
            ],
            cursor=1234567890,
            has_more=True,
        )

        monkeypatch.setattr(
            "app.services.tiktok.videos.fetch_video_page",
            lambda **_: page,
        )

        result = sync_video_page(db, account, max_count=20)
        assert result.cursor == 1234567890
        assert result.has_more is True

        video = db.scalar(
            select(TikTokVideo).where(
                TikTokVideo.account_id == account.id,
                TikTokVideo.video_id == "video-123",
            )
        )
        assert video is not None
        assert video.title == "Video title"
        assert video.view_count == 100
        assert video.like_count == 10
        assert video.cover_image_url == "https://example.com/cover.jpg"

        db.execute(delete(TikTokVideo).where(TikTokVideo.account_id == account.id))
        db.delete(account)
        db.commit()
