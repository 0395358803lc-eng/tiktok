from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TikTokPublishJob(Base):
    __tablename__ = "tiktok_publish_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("tiktok_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    media_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    media_type: Mapped[str] = mapped_column(String(16))
    source_type: Mapped[str] = mapped_column(String(32))
    source_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    privacy_level: Mapped[str] = mapped_column(String(40))
    disable_comment: Mapped[bool] = mapped_column(Boolean)
    disable_duet: Mapped[bool] = mapped_column(Boolean)
    disable_stitch: Mapped[bool] = mapped_column(Boolean)
    auto_add_music: Mapped[bool] = mapped_column(Boolean)
    brand_content_toggle: Mapped[bool] = mapped_column(Boolean)
    brand_organic_toggle: Mapped[bool] = mapped_column(Boolean)
    is_aigc: Mapped[bool] = mapped_column(Boolean)
    video_cover_timestamp_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consent_music_usage: Mapped[bool] = mapped_column(Boolean)
    consent_branded_policy: Mapped[bool] = mapped_column(Boolean)
    creator_info_json: Mapped[str] = mapped_column(Text)
    publish_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    fail_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    downloaded_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    public_post_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
