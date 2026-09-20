from dataclasses import dataclass

import httpx

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
REVOKE_URL = "https://open.tiktokapis.com/v2/oauth/revoke/"


class TikTokOAuthError(RuntimeError):
    pass


@dataclass(slots=True)
class TokenResponse:
    open_id: str
    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    scope: str
    token_type: str


def _parse_token_response(response: httpx.Response) -> TokenResponse:
    try:
        payload = response.json()
    except ValueError as exc:
        raise TikTokOAuthError("TikTok returned a non-JSON response") from exc

    if response.is_error or "error" in payload:
        message = payload.get("error_description") or payload.get("error") or "OAuth request failed"
        raise TikTokOAuthError(str(message))

    required = {
        "open_id", "access_token", "refresh_token", "expires_in",
        "refresh_expires_in", "scope", "token_type",
    }
    if not required.issubset(payload):
        raise TikTokOAuthError("TikTok token response is missing required fields")

    return TokenResponse(
        open_id=str(payload["open_id"]),
        access_token=str(payload["access_token"]),
        refresh_token=str(payload["refresh_token"]),
        expires_in=int(payload["expires_in"]),
        refresh_expires_in=int(payload["refresh_expires_in"]),
        scope=str(payload["scope"]),
        token_type=str(payload["token_type"]),
    )


def exchange_code(
    *, client_key: str, client_secret: str, code: str, redirect_uri: str
) -> TokenResponse:
    response = httpx.post(
        TOKEN_URL,
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    return _parse_token_response(response)


def refresh_access_token(
    *, client_key: str, client_secret: str, refresh_token: str
) -> TokenResponse:
    response = httpx.post(
        TOKEN_URL,
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    return _parse_token_response(response)


def revoke_access(*, client_key: str, client_secret: str, access_token: str) -> None:
    response = httpx.post(
        REVOKE_URL,
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "token": access_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if response.is_error:
        try:
            payload = response.json()
            message = payload.get("error_description") or payload.get("error")
        except ValueError:
            message = None
        raise TikTokOAuthError(str(message or "TikTok revoke request failed"))
