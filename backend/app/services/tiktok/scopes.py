from dataclasses import dataclass

from app.core.settings import Settings

BASIC_SCOPE = "user.info.basic"
PROFILE_SCOPE = "user.info.profile"
STATS_SCOPE = "user.info.stats"

PERSONAL_SCOPES = (BASIC_SCOPE, PROFILE_SCOPE, STATS_SCOPE)

BASIC_FIELDS = ("open_id", "union_id", "avatar_url", "display_name")
PROFILE_FIELDS = ("username", "bio_description", "profile_deep_link", "is_verified")
STATS_FIELDS = ("follower_count", "following_count", "likes_count", "video_count")


@dataclass(frozen=True, slots=True)
class ScopeCapability:
    scope: str
    label: str
    description: str


SCOPE_CATALOG = (
    ScopeCapability(
        scope=BASIC_SCOPE,
        label="Basic profile",
        description="Open ID, avatar and display name.",
    ),
    ScopeCapability(
        scope=PROFILE_SCOPE,
        label="Extended profile",
        description="Username, bio, profile link and verification status.",
    ),
    ScopeCapability(
        scope=STATS_SCOPE,
        label="Profile statistics",
        description="Follower, following, likes and public video counts.",
    ),
)


def normalize_scopes(raw: str | list[str] | tuple[str, ...]) -> list[str]:
    items = raw.split(",") if isinstance(raw, str) else raw
    ordered: list[str] = []
    for item in items:
        scope = item.strip()
        if scope and scope not in ordered:
            ordered.append(scope)
    return ordered


def configured_personal_scopes(settings: Settings) -> list[str]:
    configured = normalize_scopes(settings.tiktok_scopes)
    return [scope for scope in PERSONAL_SCOPES if scope in configured]


def validate_requested_scopes(
    requested: list[str] | None,
    settings: Settings,
) -> list[str]:
    configured = configured_personal_scopes(settings)
    if not configured:
        raise ValueError("No supported TikTok personal scopes are configured")

    if requested is None:
        return configured

    normalized = normalize_scopes(requested)
    unsupported = [scope for scope in normalized if scope not in PERSONAL_SCOPES]
    if unsupported:
        raise ValueError(f"Unsupported TikTok scope: {unsupported[0]}")

    unavailable = [scope for scope in normalized if scope not in configured]
    if unavailable:
        raise ValueError(f"TikTok scope is not enabled for this app: {unavailable[0]}")

    if BASIC_SCOPE not in normalized:
        normalized.insert(0, BASIC_SCOPE)

    return [scope for scope in PERSONAL_SCOPES if scope in normalized]


def user_info_fields(scopes: str | list[str]) -> list[str]:
    granted = set(normalize_scopes(scopes))
    fields = list(BASIC_FIELDS)
    if PROFILE_SCOPE in granted:
        fields.extend(PROFILE_FIELDS)
    if STATS_SCOPE in granted:
        fields.extend(STATS_FIELDS)
    return fields
