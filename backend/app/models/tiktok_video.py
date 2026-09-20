from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TikTokVideo(Base):
    __tablename__ = "tiktok_videos"
    __table_args__ = (
        UniqueConstraint("account_id", "video_id", name="uq_tiktok_video_account_video"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("tiktok_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    video_id: Mapped[str] = mapped_column(String(128), index=True)
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    share_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embed_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    like_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    comment_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    share_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    view_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_aigc: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
