from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import AccountStatSnapshot, VideoMetricSnapshot
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_video import TikTokVideo

DEDUPE_WINDOW_SECONDS = 300


def _same_account_metrics(
    snapshot: AccountStatSnapshot,
    account: TikTokAccount,
) -> bool:
    return (
        snapshot.follower_count == account.follower_count
        and snapshot.following_count == account.following_count
        and snapshot.likes_count == account.likes_count
        and snapshot.video_count == account.video_count
    )


def capture_account_snapshot(
    db: Session,
    account: TikTokAccount,
    *,
    captured_at: datetime | None = None,
) -> AccountStatSnapshot | None:
    metrics = (
        account.follower_count,
        account.following_count,
        account.likes_count,
        account.video_count,
    )
    if all(value is None for value in metrics):
        return None

    now = captured_at or datetime.now(UTC)
    latest = db.scalar(
        select(AccountStatSnapshot)
        .where(AccountStatSnapshot.account_id == account.id)
        .order_by(AccountStatSnapshot.captured_at.desc())
        .limit(1)
    )
    if (
        latest is not None
        and now - latest.captured_at < timedelta(seconds=DEDUPE_WINDOW_SECONDS)
        and _same_account_metrics(latest, account)
    ):
        return None

    snapshot = AccountStatSnapshot(
        account_id=account.id,
        captured_at=now,
        follower_count=account.follower_count,
        following_count=account.following_count,
        likes_count=account.likes_count,
        video_count=account.video_count,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def _same_video_metrics(
    snapshot: VideoMetricSnapshot,
    video: TikTokVideo,
) -> bool:
    return (
        snapshot.like_count == video.like_count
        and snapshot.comment_count == video.comment_count
        and snapshot.share_count == video.share_count
        and snapshot.view_count == video.view_count
    )


def capture_video_snapshots(
    db: Session,
    *,
    account_id: int,
    video_ids: list[str],
    captured_at: datetime | None = None,
) -> int:
    if not video_ids:
        return 0

    now = captured_at or datetime.now(UTC)
    videos = db.scalars(
        select(TikTokVideo).where(
            TikTokVideo.account_id == account_id,
            TikTokVideo.video_id.in_(video_ids),
        )
    ).all()

    created = 0
    for video in videos:
        metrics = (
            video.like_count,
            video.comment_count,
            video.share_count,
            video.view_count,
        )
        if all(value is None for value in metrics):
            continue

        latest = db.scalar(
            select(VideoMetricSnapshot)
            .where(VideoMetricSnapshot.video_pk == video.id)
            .order_by(VideoMetricSnapshot.captured_at.desc())
            .limit(1)
        )
        if (
            latest is not None
            and now - latest.captured_at < timedelta(seconds=DEDUPE_WINDOW_SECONDS)
            and _same_video_metrics(latest, video)
        ):
            continue

        db.add(
            VideoMetricSnapshot(
                video_pk=video.id,
                account_id=account_id,
                video_id=video.video_id,
                captured_at=now,
                like_count=video.like_count,
                comment_count=video.comment_count,
                share_count=video.share_count,
                view_count=video.view_count,
            )
        )
        created += 1

    if created:
        db.commit()
    return created


def _delta(first: int | None, last: int | None) -> int | None:
    if first is None or last is None:
        return None
    return last - first


def build_analytics_report(
    db: Session,
    *,
    account_id: int,
    days: int,
) -> dict:
    cutoff = datetime.now(UTC) - timedelta(days=days)

    account_points = db.scalars(
        select(AccountStatSnapshot)
        .where(
            AccountStatSnapshot.account_id == account_id,
            AccountStatSnapshot.captured_at >= cutoff,
        )
        .order_by(AccountStatSnapshot.captured_at.asc())
    ).all()

    account_deltas = {
        "followers": None,
        "following": None,
        "likes": None,
        "videos": None,
    }
    if len(account_points) >= 2:
        first = account_points[0]
        last = account_points[-1]
        account_deltas = {
            "followers": _delta(first.follower_count, last.follower_count),
            "following": _delta(first.following_count, last.following_count),
            "likes": _delta(first.likes_count, last.likes_count),
            "videos": _delta(first.video_count, last.video_count),
        }

    video_rows = db.scalars(
        select(VideoMetricSnapshot)
        .where(
            VideoMetricSnapshot.account_id == account_id,
            VideoMetricSnapshot.captured_at >= cutoff,
        )
        .order_by(
            VideoMetricSnapshot.video_pk.asc(),
            VideoMetricSnapshot.captured_at.asc(),
        )
    ).all()

    grouped: dict[int, list[VideoMetricSnapshot]] = defaultdict(list)
    for row in video_rows:
        grouped[row.video_pk].append(row)

    video_ids = list(grouped)
    videos = (
        db.scalars(select(TikTokVideo).where(TikTokVideo.id.in_(video_ids))).all()
        if video_ids
        else []
    )
    video_map = {video.id: video for video in videos}

    top_videos = []
    for video_pk, snapshots in grouped.items():
        video = video_map.get(video_pk)
        if video is None:
            continue
        first = snapshots[0]
        last = snapshots[-1]
        top_videos.append(
            {
                "video_id": video.video_id,
                "title": video.title,
                "share_url": video.share_url,
                "cover_image_url": video.cover_image_url,
                "view_count": last.view_count,
                "like_count": last.like_count,
                "comment_count": last.comment_count,
                "share_count": last.share_count,
                "view_delta": _delta(first.view_count, last.view_count),
                "like_delta": _delta(first.like_count, last.like_count),
                "comment_delta": _delta(first.comment_count, last.comment_count),
                "share_delta": _delta(first.share_count, last.share_count),
                "first_captured_at": first.captured_at,
                "last_captured_at": last.captured_at,
            }
        )

    top_videos.sort(
        key=lambda item: (
            item["view_delta"] if item["view_delta"] is not None else -1,
            item["view_count"] if item["view_count"] is not None else -1,
        ),
        reverse=True,
    )

    return {
        "account_id": account_id,
        "days": days,
        "account_points": [
            {
                "captured_at": point.captured_at,
                "follower_count": point.follower_count,
                "following_count": point.following_count,
                "likes_count": point.likes_count,
                "video_count": point.video_count,
            }
            for point in account_points
        ],
        "account_deltas": account_deltas,
        "top_videos": top_videos[:20],
        "account_snapshot_count": len(account_points),
        "video_snapshot_count": len(video_rows),
    }
