from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "TH TikTok Manager API"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 18000
    frontend_origin: str = "http://localhost:15173"

    database_url: str
    cache_url: str
    app_secret: SecretStr
    token_encryption_key: SecretStr
    admin_username: str = "admin"
    admin_password: SecretStr
    session_ttl_seconds: int = 43200

    tiktok_environment: str = "sandbox"
    tiktok_client_key: str | None = None
    tiktok_sandbox_client_key: str | None = None
    tiktok_sandbox_client_secret: SecretStr | None = None
    tiktok_production_client_key: str | None = None
    tiktok_production_client_secret: SecretStr | None = None
    tiktok_client_secret: SecretStr | None = None
    tiktok_redirect_uri: str | None = None
    tiktok_scopes: str = "user.info.basic"
    oauth_state_ttl_seconds: int = 600
    oauth_session_retention_seconds: int = 86400
    token_refresh_interval_seconds: int = 300
    token_refresh_lead_seconds: int = 7200

    @property
    def active_tiktok_client_key(self) -> str | None:
        if self.tiktok_environment.lower() == "production":
            return self.tiktok_production_client_key or self.tiktok_client_key
        return self.tiktok_sandbox_client_key or self.tiktok_client_key

    @property
    def active_tiktok_client_secret(self) -> SecretStr | None:
        if self.tiktok_environment.lower() == "production":
            return self.tiktok_production_client_secret or self.tiktok_client_secret
        return self.tiktok_sandbox_client_secret or self.tiktok_client_secret

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
