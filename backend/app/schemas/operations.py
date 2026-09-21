from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AccountOperationsSummary(BaseModel):
    account_id: int
    display_name: str | None
    username: str | None
    status: str
    scopes: list[str]
    missing_configured_scopes: list[str]
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    access_token_minutes_left: int
    refresh_token_days_left: int
    profile_synced_at: datetime | None
    profile_age_hours: float | None
    stored_videos: int
    scheduled_posts: int
    running_posts: int
    failed_posts: int
    failed_drafts: int
    webhook_errors: int
    health: Literal["OK", "WARNING", "ERROR"]
    issues: list[str]


class OperationsSummary(BaseModel):
    generated_at: datetime
    accounts_total: int
    connected_accounts: int
    reauth_accounts: int
    issue_accounts: int
    scheduled_posts: int
    running_posts: int
    failed_posts: int
    pending_webhooks: int
    error_webhooks: int
    accounts: list[AccountOperationsSummary]


class BulkOperationRequest(BaseModel):
    action: Literal["REFRESH_TOKENS", "SYNC_PROFILE", "SYNC_VIDEOS"]
    account_ids: list[int] = Field(min_length=1, max_length=50)


class BulkOperationResult(BaseModel):
    account_id: int
    ok: bool
    detail: str


class BulkOperationResponse(BaseModel):
    action: str
    requested: int
    succeeded: int
    failed: int
    results: list[BulkOperationResult]


class ReadinessCheck(BaseModel):
    key: str
    label: str
    status: Literal["PASS", "WARN", "FAIL"]
    detail: str


class ProductionReadinessReport(BaseModel):
    generated_at: datetime
    status: Literal["READY", "NOT_READY"]
    pass_count: int
    warn_count: int
    fail_count: int
    checks: list[ReadinessCheck]
