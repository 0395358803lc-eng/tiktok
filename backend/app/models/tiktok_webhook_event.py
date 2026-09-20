from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TikTokWebhookEvent(Base):
    __tablename__ = "tiktok_webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dedup_hash: Mapped[str] = mapped_column(String(64), unique=True)
    client_key: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    user_open_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    content_json: Mapped[str] = mapped_column(Text)
    signature_timestamp: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(24), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
