from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, select

from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.oauth_session import OAuthSession
from app.models.tiktok_account import TikTokAccount
from app.services.tiktok.client import TokenResponse
from app.services.tiktok.crypto import decrypt_token, encrypt_token
from app.services.tiktok.oauth import build_authorize_url, state_digest

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


def test_oauth_configuration_gate():
    _login()
    config = client.get("/api/tiktok/config")
    assert config.status_code == 200
    assert config.json()["configured"] is False

    start = client.post("/api/tiktok/oauth/start")
    assert start.status_code == 503


def test_authorize_url_contains_expected_web_oauth_fields():
    settings = get_settings().model_copy(
        update={
            "tiktok_client_key": "client-key",
            "tiktok_client_secret": SecretStr("client-secret"),
            "tiktok_redirect_uri": "https://example.com/api/tiktok/oauth/callback",
            "tiktok_scopes": "user.info.basic,video.list",
        }
    )
    url = build_authorize_url(settings, "csrf-state")
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "www.tiktok.com"
    assert query["response_type"] == ["code"]
    assert query["state"] == ["csrf-state"]
    assert "client-secret" not in url


def test_token_encryption_round_trip():
    encrypted = encrypt_token("secret-token")
    assert encrypted != "secret-token"
    assert decrypt_token(encrypted) == "secret-token"


def test_callback_rejects_invalid_state():
    response = client.get(
        "/api/tiktok/oauth/callback",
        params={"code": "unused", "state": "invalid-state"},
        follow_redirects=False,
    )
    assert response.status_code in {302, 307}
    assert "tiktok=error" in response.headers["location"]


def test_callback_stores_encrypted_tokens(monkeypatch):
    raw_state = "test-oauth-state"
    now = datetime.now(UTC)
    with SessionLocal() as db:
        db.execute(delete(TikTokAccount).where(TikTokAccount.open_id == "test-open-id"))
        db.execute(delete(OAuthSession).where(OAuthSession.state_hash == state_digest(raw_state)))
        db.add(
            OAuthSession(
                state_hash=state_digest(raw_state),
                created_at=now,
                expires_at=now + timedelta(minutes=5),
            )
        )
        db.commit()

    settings = get_settings()
    original_key = settings.tiktok_client_key
    original_secret = settings.tiktok_client_secret
    original_redirect = settings.tiktok_redirect_uri
    settings.tiktok_client_key = "client-key"
    settings.tiktok_client_secret = SecretStr("client-secret")
    settings.tiktok_redirect_uri = "https://example.com/api/tiktok/oauth/callback"

    monkeypatch.setattr(
        "app.api.tiktok.exchange_code",
        lambda **_: TokenResponse(
            open_id="test-open-id",
            access_token="raw-access",
            refresh_token="raw-refresh",
            expires_in=86400,
            refresh_expires_in=31536000,
            scope="user.info.basic",
            token_type="Bearer",
        ),
    )
    try:
        response = client.get(
            "/api/tiktok/oauth/callback",
            params={"code": "auth-code", "state": raw_state},
            follow_redirects=False,
        )
        assert response.status_code in {302, 307}
        assert "tiktok=connected" in response.headers["location"]

        with SessionLocal() as db:
            account = db.scalar(
                select(TikTokAccount).where(TikTokAccount.open_id == "test-open-id")
            )
            assert account is not None
            assert account.access_token_enc != "raw-access"
            assert account.refresh_token_enc != "raw-refresh"
            assert decrypt_token(account.access_token_enc) == "raw-access"
            assert decrypt_token(account.refresh_token_enc) == "raw-refresh"
            db.delete(account)
            db.execute(delete(OAuthSession).where(OAuthSession.state_hash == state_digest(raw_state)))
            db.commit()
    finally:
        settings.tiktok_client_key = original_key
        settings.tiktok_client_secret = original_secret
        settings.tiktok_redirect_uri = original_redirect


def test_refresh_replaces_rotated_refresh_token(monkeypatch):
    from app.services.tiktok.tokens import refresh_account_tokens

    settings = get_settings()
    original_key = settings.tiktok_client_key
    original_secret = settings.tiktok_client_secret
    original_redirect = settings.tiktok_redirect_uri
    settings.tiktok_client_key = "client-key"
    settings.tiktok_client_secret = SecretStr("client-secret")
    settings.tiktok_redirect_uri = "https://example.com/api/tiktok/oauth/callback"

    now = datetime.now(UTC)
    with SessionLocal() as db:
        db.execute(delete(TikTokAccount).where(TikTokAccount.open_id == "refresh-open-id"))
        account = TikTokAccount(
            open_id="refresh-open-id",
            scopes="user.info.basic",
            access_token_enc=encrypt_token("old-access"),
            refresh_token_enc=encrypt_token("old-refresh"),
            access_token_expires_at=now,
            refresh_token_expires_at=now + timedelta(days=30),
            status="CONNECTED",
            created_at=now,
            updated_at=now,
        )
        db.add(account)
        db.commit()

        monkeypatch.setattr(
            "app.services.tiktok.tokens.refresh_access_token",
            lambda **_: TokenResponse(
                open_id="refresh-open-id",
                access_token="new-access",
                refresh_token="new-refresh",
                expires_in=86400,
                refresh_expires_in=31536000,
                scope="user.info.basic",
                token_type="Bearer",
            ),
        )
        try:
            refresh_account_tokens(db, account)
            assert decrypt_token(account.access_token_enc) == "new-access"
            assert decrypt_token(account.refresh_token_enc) == "new-refresh"
            assert account.last_token_refresh_at is not None
        finally:
            db.delete(account)
            db.commit()
            settings.tiktok_client_key = original_key
            settings.tiktok_client_secret = original_secret
            settings.tiktok_redirect_uri = original_redirect
