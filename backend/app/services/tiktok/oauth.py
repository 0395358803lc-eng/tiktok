import hashlib
import secrets
from urllib.parse import urlencode

from app.core.settings import Settings
from app.services.tiktok.scopes import validate_requested_scopes

AUTHORIZE_URL = "https://www.tiktok.com/v2/auth/authorize/"


def oauth_configured(settings: Settings) -> bool:
    return bool(
        settings.active_tiktok_client_key
        and settings.active_tiktok_client_secret
        and settings.active_tiktok_client_secret.get_secret_value()
        and settings.tiktok_redirect_uri
    )


def new_state() -> str:
    return secrets.token_urlsafe(32)


def state_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_authorize_url(
    settings: Settings,
    state: str,
    scopes: list[str] | None = None,
) -> str:
    if not oauth_configured(settings):
        raise ValueError("TikTok OAuth is not configured")

    requested_scopes = validate_requested_scopes(scopes, settings)
    query = urlencode(
        {
            "client_key": settings.active_tiktok_client_key,
            "response_type": "code",
            "scope": ",".join(requested_scopes),
            "redirect_uri": settings.tiktok_redirect_uri,
            "state": state,
        }
    )
    return f"{AUTHORIZE_URL}?{query}"
