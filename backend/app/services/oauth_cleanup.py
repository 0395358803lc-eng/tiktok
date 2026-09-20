from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, or_
from sqlalchemy.orm import Session

from app.models.oauth_session import OAuthSession


def cleanup_oauth_sessions(db: Session, retention_seconds: int) -> int:
    now = datetime.now(UTC)
    consumed_cutoff = now - timedelta(seconds=retention_seconds)
    result = db.execute(
        delete(OAuthSession).where(
            or_(
                OAuthSession.expires_at < now,
                OAuthSession.consumed_at < consumed_cutoff,
            )
        )
    )
    db.commit()
    return int(result.rowcount or 0)
