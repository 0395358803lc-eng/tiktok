from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TikTokAccount(Base):
    __tablename__ = "tiktok_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    open_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    union_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    scopes: Mapped[str] = mapped_column(Text, default="")
    access_token_enc: Mapped[str] = mapped_column(Text)
    refresh_token_enc: Mapped[str] = mapped_column(Text)
    access_token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    refresh_token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="CONNECTED", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_token_refresh_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    profile_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
