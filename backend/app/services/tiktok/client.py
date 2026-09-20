from dataclasses import dataclass

import httpx

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
REVOKE_URL = "https://open.tiktokapis.com/v2/oauth/revoke/"
USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"


class TikTokOAuthError(RuntimeError):
    pass


class TikTokAPIError(RuntimeError):
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


@dataclass(slots=True)
class UserInfoResponse:
    open_id: str
    union_id: str | None
    display_name: str | None
    avatar_url: str | None


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


def get_user_info(*, access_token: str) -> UserInfoResponse:
    response = httpx.get(
        USER_INFO_URL,
        params={"fields": "open_id,union_id,avatar_url,display_name"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    try:
        payload = response.json()
    except ValueError as exc:
        raise TikTokAPIError("TikTok returned a non-JSON user-info response") from exc

    error = payload.get("error") or {}
    error_code = error.get("code")
    if response.is_error or error_code not in (None, 0, "ok"):
        message = error.get("message") or "TikTok user-info request failed"
        raise TikTokAPIError(str(message))

    user = (payload.get("data") or {}).get("user") or {}
    open_id = user.get("open_id")
    if not open_id:
        raise TikTokAPIError("TikTok user-info response is missing open_id")

    return UserInfoResponse(
        open_id=str(open_id),
        union_id=str(user["union_id"]) if user.get("union_id") else None,
        display_name=str(user["display_name"]) if user.get("display_name") else None,
        avatar_url=str(user["avatar_url"]) if user.get("avatar_url") else None,
    )
