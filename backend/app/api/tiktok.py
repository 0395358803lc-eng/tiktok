from datetime import UTC, datetime, timedelta
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.api.auth import DbSession, require_admin
from app.core.settings import get_settings
from app.models.admin_session import AdminSession
from app.models.oauth_session import OAuthSession
from app.models.tiktok_account import TikTokAccount
from app.schemas.tiktok import OAuthStartResponse, TikTokAccountSummary, TikTokConfigStatus
from app.services.tiktok.client import (
    TikTokOAuthError,
    exchange_code,
    revoke_access,
)
from app.services.tiktok.crypto import decrypt_token, encrypt_token
from app.services.tiktok.oauth import build_authorize_url, new_state, oauth_configured, state_digest
from app.services.tiktok.tokens import (
    TikTokConfigurationError,
    TikTokIdentityError,
    refresh_account_tokens,
)

router = APIRouter(prefix="/tiktok", tags=["tiktok"])
Admin = Annotated[AdminSession, Depends(require_admin)]


def _scope_list(raw: str) -> list[str]:
    return [scope for scope in (item.strip() for item in raw.split(",")) if scope]


def _frontend_redirect(kind: str, message: str | None = None) -> RedirectResponse:
    settings = get_settings()
    params = {"tiktok": kind}
    if message:
        params["message"] = message[:160]
    return RedirectResponse(f"{settings.frontend_origin}/?{urlencode(params)}")


@router.get("/config", response_model=TikTokConfigStatus)
def config_status(_: Admin):
    settings = get_settings()
    return TikTokConfigStatus(
        configured=oauth_configured(settings),
        scopes=_scope_list(settings.tiktok_scopes),
        redirect_uri=settings.tiktok_redirect_uri or None,
    )


@router.post("/oauth/start", response_model=OAuthStartResponse)
def oauth_start(_: Admin, db: DbSession):
    settings = get_settings()
    if not oauth_configured(settings):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TikTok OAuth is not configured",
        )

    raw_state = new_state()
    now = datetime.now(UTC)
    db.add(
        OAuthSession(
            state_hash=state_digest(raw_state),
            created_at=now,
            expires_at=now + timedelta(seconds=settings.oauth_state_ttl_seconds),
        )
    )
    db.commit()
    return OAuthStartResponse(
        authorize_url=build_authorize_url(settings, raw_state),
    )


@router.get("/oauth/callback")
def oauth_callback(
    db: DbSession,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
):
    if not state:
        return _frontend_redirect("error", "Missing OAuth state")

    now = datetime.now(UTC)
    oauth_session = db.scalar(
        select(OAuthSession).where(
            OAuthSession.state_hash == state_digest(state),
            OAuthSession.consumed_at.is_(None),
            OAuthSession.expires_at > now,
        )
    )
    if oauth_session is None:
        return _frontend_redirect("error", "Invalid or expired OAuth state")

    oauth_session.consumed_at = now
    db.commit()

    if error:
        return _frontend_redirect("error", error_description or error)

    if not code:
        return _frontend_redirect("error", "Missing authorization code")

    settings = get_settings()
    if not oauth_configured(settings):
        return _frontend_redirect("error", "TikTok OAuth configuration is unavailable")

    client_secret = settings.tiktok_client_secret
    if client_secret is None or settings.tiktok_client_key is None or settings.tiktok_redirect_uri is None:
        return _frontend_redirect("error", "TikTok OAuth configuration is incomplete")

    try:
        token = exchange_code(
            client_key=settings.tiktok_client_key,
            client_secret=client_secret.get_secret_value(),
            code=code,
            redirect_uri=settings.tiktok_redirect_uri,
        )
    except TikTokOAuthError as exc:
        return _frontend_redirect("error", str(exc))
    except httpx.RequestError:
        return _frontend_redirect("error", "TikTok token endpoint is unavailable")

    now = datetime.now(UTC)
    account = db.scalar(
        select(TikTokAccount).where(TikTokAccount.open_id == token.open_id)
    )
    if account is None:
        account = TikTokAccount(
            open_id=token.open_id,
            access_token_enc="",
            refresh_token_enc="",
            access_token_expires_at=now,
            refresh_token_expires_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(account)

    account.scopes = token.scope
    account.access_token_enc = encrypt_token(token.access_token)
    account.refresh_token_enc = encrypt_token(token.refresh_token)
    account.access_token_expires_at = now + timedelta(seconds=token.expires_in)
    account.refresh_token_expires_at = now + timedelta(seconds=token.refresh_expires_in)
    account.status = "CONNECTED"
    account.updated_at = now
    db.commit()

    return _frontend_redirect("connected")


@router.get("/accounts", response_model=list[TikTokAccountSummary])
def list_accounts(_: Admin, db: DbSession):
    rows = db.scalars(select(TikTokAccount).order_by(TikTokAccount.id.desc())).all()
    return [
        TikTokAccountSummary(
            id=row.id,
            open_id=row.open_id,
            scopes=_scope_list(row.scopes),
            status=row.status,
            access_token_expires_at=row.access_token_expires_at,
            refresh_token_expires_at=row.refresh_token_expires_at,
            last_token_refresh_at=row.last_token_refresh_at,
        )
        for row in rows
    ]


def _client_credentials() -> tuple[str, str]:
    settings = get_settings()
    if (
        not oauth_configured(settings)
        or settings.tiktok_client_key is None
        or settings.tiktok_client_secret is None
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TikTok OAuth is not configured",
        )
    return settings.tiktok_client_key, settings.tiktok_client_secret.get_secret_value()


@router.post("/accounts/{account_id}/refresh", response_model=TikTokAccountSummary)
def refresh_account(account_id: int, _: Admin, db: DbSession):
    account = db.get(TikTokAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="TikTok account not found")

    try:
        refresh_account_tokens(db, account)
    except TikTokConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except TikTokOAuthError as exc:
        account.status = "REAUTH_REQUIRED"
        account.updated_at = datetime.now(UTC)
        db.commit()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except TikTokIdentityError as exc:
        account.status = "ERROR"
        account.updated_at = datetime.now(UTC)
        db.commit()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        account.status = "ERROR"
        account.updated_at = datetime.now(UTC)
        db.commit()
        raise HTTPException(status_code=502, detail="TikTok token endpoint unavailable") from exc

    return TikTokAccountSummary(
        id=account.id,
        open_id=account.open_id,
        scopes=_scope_list(account.scopes),
        status=account.status,
        access_token_expires_at=account.access_token_expires_at,
        refresh_token_expires_at=account.refresh_token_expires_at,
        last_token_refresh_at=account.last_token_refresh_at,
    )


@router.post("/accounts/{account_id}/disconnect", response_model=TikTokAccountSummary)
def disconnect_account(account_id: int, _: Admin, db: DbSession):
    account = db.get(TikTokAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="TikTok account not found")

    client_key, client_secret = _client_credentials()
    try:
        revoke_access(
            client_key=client_key,
            client_secret=client_secret,
            access_token=decrypt_token(account.access_token_enc),
        )
    except TikTokOAuthError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="TikTok revoke endpoint unavailable") from exc

    account.status = "REVOKED"
    account.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(account)
    return TikTokAccountSummary(
        id=account.id,
        open_id=account.open_id,
        scopes=_scope_list(account.scopes),
        status=account.status,
        access_token_expires_at=account.access_token_expires_at,
        refresh_token_expires_at=account.refresh_token_expires_at,
        last_token_refresh_at=account.last_token_refresh_at,
    )
