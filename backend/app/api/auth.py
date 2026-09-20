from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.security import new_session_token, token_digest, verify_password
from app.core.settings import get_settings
from app.db.session import get_db
from app.models.admin_session import AdminSession
from app.schemas.auth import AuthStatus, LoginRequest
from app.services.audit import record_audit

router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE_NAME = "th_admin_session"
DbSession = Annotated[Session, Depends(get_db)]
AdminCookie = Annotated[str | None, Cookie(alias=COOKIE_NAME)]


def _session_from_token(db: Session, token: str | None) -> AdminSession | None:
    if not token:
        return None
    stmt = select(AdminSession).where(
        AdminSession.token_hash == token_digest(token),
        AdminSession.expires_at > datetime.now(UTC),
    )
    return db.scalar(stmt)


@router.post("/login", response_model=AuthStatus)
def login(payload: LoginRequest, response: Response, db: DbSession):
    settings = get_settings()
    valid_user = payload.username == settings.admin_username
    valid_password = verify_password(
        payload.password,
        settings.admin_password.get_secret_value(),
    )
    if not (valid_user and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    raw_token = new_session_token()
    now = datetime.now(UTC)
    session = AdminSession(
        token_hash=token_digest(raw_token),
        username=payload.username,
        created_at=now,
        expires_at=now + timedelta(seconds=settings.session_ttl_seconds),
    )
    db.add(session)
    db.commit()
    record_audit(
        db,
        event_type="ADMIN_LOGIN",
        actor=payload.username,
        detail="Admin session created",
    )

    response.set_cookie(
        COOKIE_NAME,
        raw_token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    return AuthStatus(authenticated=True, username=payload.username)


@router.get("/me", response_model=AuthStatus)
def me(db: DbSession, th_admin_session: AdminCookie = None):
    session = _session_from_token(db, th_admin_session)
    if session is None:
        return AuthStatus(authenticated=False)
    return AuthStatus(authenticated=True, username=session.username)


@router.post("/logout", response_model=AuthStatus)
def logout(response: Response, db: DbSession, th_admin_session: AdminCookie = None):
    actor = "admin"
    if th_admin_session:
        session = _session_from_token(db, th_admin_session)
        if session is not None:
            actor = session.username
        db.execute(
            delete(AdminSession).where(
                AdminSession.token_hash == token_digest(th_admin_session)
            )
        )
        db.commit()
        record_audit(
            db,
            event_type="ADMIN_LOGOUT",
            actor=actor,
            detail="Admin session ended",
        )

    response.delete_cookie(COOKIE_NAME, path="/")
    return AuthStatus(authenticated=False)


def require_admin(db: DbSession, th_admin_session: AdminCookie = None) -> AdminSession:
    session = _session_from_token(db, th_admin_session)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
        )
    return session
