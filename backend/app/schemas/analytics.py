from datetime import datetime

from pydantic import BaseModel


class AccountAnalyticsPoint(BaseModel):
    captured_at: datetime
    follower_count: int | None
    following_count: int | None
    likes_count: int | None
    video_count: int | None


class AnalyticsDelta(BaseModel):
    followers: int | None
    following: int | None
    likes: int | None
    videos: int | None


class VideoAnalyticsSummary(BaseModel):
    video_id: str
    title: str | None
    share_url: str | None
    cover_image_url: str | None
    view_count: int | None
    like_count: int | None
    comment_count: int | None
    share_count: int | None
    view_delta: int | None
    like_delta: int | None
    comment_delta: int | None
    share_delta: int | None
    first_captured_at: datetime
    last_captured_at: datetime


class TikTokAnalyticsReport(BaseModel):
    account_id: int
    days: int
    account_points: list[AccountAnalyticsPoint]
    account_deltas: AnalyticsDelta
    top_videos: list[VideoAnalyticsSummary]
    account_snapshot_count: int
    video_snapshot_count: int
