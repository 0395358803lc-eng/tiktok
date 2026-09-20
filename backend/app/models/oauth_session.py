from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OAuthSession(Base):
    __tablename__ = "oauth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_scopes: Mapped[str | None] = mapped_column(Text, nullable=True)
