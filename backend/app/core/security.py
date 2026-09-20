import hashlib
import hmac
import secrets


def verify_password(password: str, expected_password: str) -> bool:
    return hmac.compare_digest(
        password.encode("utf-8"),
        expected_password.encode("utf-8"),
    )


def new_session_token() -> str:
    return secrets.token_urlsafe(48)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
