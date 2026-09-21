from typing import Literal

from pydantic import BaseModel


class ScopeReviewItem(BaseModel):
    scope: str
    product: str
    feature: str
    configured: bool
    connected_accounts_with_scope: int
    code_implemented: bool
    evidence_routes: list[str]
    status: Literal["PASS", "BLOCKED", "NOT_CONFIGURED"]


class ReviewCheck(BaseModel):
    key: str
    label: str
    status: Literal["PASS", "WARN", "FAIL", "MANUAL"]
    detail: str


class ReviewPackageReport(BaseModel):
    status: Literal["READY_FOR_REVIEW", "NOT_READY_FOR_REVIEW"]
    products: list[str]
    scope_matrix: list[ScopeReviewItem]
    checks: list[ReviewCheck]
    demo_video_plan: list[str]
    website_url: str
    terms_url: str
    privacy_url: str
    oauth_redirect_url: str
    webhook_url: str
