from datetime import UTC, datetime, timedelta

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.analytics import AccountStatSnapshot, VideoMetricSnapshot
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_video import TikTokVideo
from app.services.analytics import (
    build_analytics_report,
    capture_account_snapshot,
    capture_video_snapshots,
)
from app.services.tiktok.crypto import encrypt_token


def _account(db) -> TikTokAccount:
    now = datetime.now(UTC)
    account = TikTokAccount(
        open_id="analytics-test-open-id",
        scopes="user.info.basic,user.info.stats,video.list",
        access_token_enc=encrypt_token("analytics-access"),
        refresh_token_enc=encrypt_token("analytics-refresh"),
        access_token_expires_at=now + timedelta(days=1),
        refresh_token_expires_at=now + timedelta(days=30),
        status="CONNECTED",
        created_at=now,
        updated_at=now,
        follower_count=100,
        following_count=20,
        likes_count=1000,
        video_count=10,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def test_account_analytics_delta():
    now = datetime.now(UTC)
    with SessionLocal() as db:
        db.execute(
            delete(TikTokAccount).where(
                TikTokAccount.open_id == "analytics-test-open-id"
            )
        )
        db.commit()
        account = _account(db)

        capture_account_snapshot(
            db,
            account,
            captured_at=now - timedelta(days=2),
        )
        account.follower_count = 125
        account.following_count = 22
        account.likes_count = 1150
        account.video_count = 12
        db.commit()
        capture_account_snapshot(
            db,
            account,
            captured_at=now - timedelta(days=1),
        )

        report = build_analytics_report(
            db,
            account_id=account.id,
            days=7,
        )
        assert report["account_snapshot_count"] == 2
        assert report["account_deltas"]["followers"] == 25
        assert report["account_deltas"]["following"] == 2
        assert report["account_deltas"]["likes"] == 150
        assert report["account_deltas"]["videos"] == 2

        db.delete(account)
        db.commit()


def test_video_analytics_delta():
    now = datetime.now(UTC)
    with SessionLocal() as db:
        account = _account(db)
        video = TikTokVideo(
            account_id=account.id,
            video_id="analytics-video-1",
            title="Analytics video",
            like_count=10,
            comment_count=2,
            share_count=1,
            view_count=100,
            synced_at=now,
        )
        db.add(video)
        db.commit()
        db.refresh(video)

        capture_video_snapshots(
            db,
            account_id=account.id,
            video_ids=[video.video_id],
            captured_at=now - timedelta(days=2),
        )
        video.like_count = 25
        video.comment_count = 7
        video.share_count = 4
        video.view_count = 250
        db.commit()
        capture_video_snapshots(
            db,
            account_id=account.id,
            video_ids=[video.video_id],
            captured_at=now - timedelta(days=1),
        )

        report = build_analytics_report(
            db,
            account_id=account.id,
            days=7,
        )
        assert report["video_snapshot_count"] == 2
        assert len(report["top_videos"]) == 1
        item = report["top_videos"][0]
        assert item["view_delta"] == 150
        assert item["like_delta"] == 15
        assert item["comment_delta"] == 5
        assert item["share_delta"] == 3

        db.execute(
            delete(VideoMetricSnapshot).where(
                VideoMetricSnapshot.account_id == account.id
            )
        )
        db.execute(
            delete(AccountStatSnapshot).where(
                AccountStatSnapshot.account_id == account.id
            )
        )
        db.delete(account)
        db.commit()
