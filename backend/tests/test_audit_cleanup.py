from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.oauth_session import OAuthSession
from app.services.oauth_cleanup import cleanup_oauth_sessions
from app.services.tiktok.oauth import state_digest

client = TestClient(app)


def _login() -> None:
    settings = get_settings()
    response = client.post(
        "/api/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password.get_secret_value(),
        },
    )
    assert response.status_code == 200


def test_audit_endpoint_requires_admin_and_lists_events():
    client.cookies.clear()
    unauthorized = client.get("/api/audit/events")
    assert unauthorized.status_code == 401

    _login()
    response = client.get("/api/audit/events?limit=20")
    assert response.status_code == 200
    events = response.json()
    assert any(event["event_type"] == "ADMIN_LOGIN" for event in events)


def test_oauth_cleanup_removes_expired_sessions_only():
    now = datetime.now(UTC)
    expired_state = state_digest("cleanup-expired")
    active_state = state_digest("cleanup-active")

    with SessionLocal() as db:
        db.execute(
            delete(OAuthSession).where(
                OAuthSession.state_hash.in_([expired_state, active_state])
            )
        )
        db.add(
            OAuthSession(
                state_hash=expired_state,
                created_at=now - timedelta(hours=2),
                expires_at=now - timedelta(hours=1),
                consumed_at=None,
            )
        )
        db.add(
            OAuthSession(
                state_hash=active_state,
                created_at=now,
                expires_at=now + timedelta(minutes=10),
                consumed_at=None,
            )
        )
        db.commit()

        removed = cleanup_oauth_sessions(db, retention_seconds=86400)
        assert removed >= 1
        assert db.scalar(
            select(OAuthSession).where(OAuthSession.state_hash == expired_state)
        ) is None
        assert db.scalar(
            select(OAuthSession).where(OAuthSession.state_hash == active_state)
        ) is not None

        db.execute(delete(OAuthSession).where(OAuthSession.state_hash == active_state))
        db.commit()
