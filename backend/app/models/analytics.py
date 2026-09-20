from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AccountStatSnapshot(Base):
    __tablename__ = "account_stat_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("tiktok_accounts.id", ondelete="CASCADE"),
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    follower_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    following_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    likes_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    video_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class VideoMetricSnapshot(Base):
    __tablename__ = "video_metric_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_pk: Mapped[int] = mapped_column(
        ForeignKey("tiktok_videos.id", ondelete="CASCADE"),
    )
    account_id: Mapped[int] = mapped_column(Integer, index=True)
    video_id: Mapped[str] = mapped_column(String(128))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    like_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    comment_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    share_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    view_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
