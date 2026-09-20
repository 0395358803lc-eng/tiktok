from pydantic import SecretStr

from app.core.settings import get_settings
from app.services.tiktok.scopes import (
    BASIC_SCOPE,
    PROFILE_SCOPE,
    STATS_SCOPE,
    configured_personal_scopes,
    user_info_fields,
    validate_requested_scopes,
)


def _settings_with_scopes(scopes: str):
    return get_settings().model_copy(
        update={
            "tiktok_scopes": scopes,
            "tiktok_client_key": "client-key",
            "tiktok_client_secret": SecretStr("client-secret"),
            "tiktok_redirect_uri": "https://example.com/api/tiktok/oauth/callback",
        }
    )


def test_configured_personal_scopes_are_ordered_and_filtered():
    settings = _settings_with_scopes(
        "user.info.stats,unknown.scope,user.info.basic,user.info.profile"
    )
    assert configured_personal_scopes(settings) == [
        BASIC_SCOPE,
        PROFILE_SCOPE,
        STATS_SCOPE,
    ]


def test_dynamic_scope_request_includes_basic_and_rejects_unconfigured():
    settings = _settings_with_scopes(
        "user.info.basic,user.info.profile,user.info.stats"
    )
    assert validate_requested_scopes([STATS_SCOPE], settings) == [
        BASIC_SCOPE,
        STATS_SCOPE,
    ]

    limited = _settings_with_scopes("user.info.basic")
    try:
        validate_requested_scopes([PROFILE_SCOPE], limited)
    except ValueError as exc:
        assert "not enabled" in str(exc)
    else:
        raise AssertionError("Expected unconfigured scope to be rejected")


def test_user_info_fields_follow_granted_scopes():
    basic = user_info_fields(BASIC_SCOPE)
    assert basic == ["open_id", "union_id", "avatar_url", "display_name"]

    profile = user_info_fields(f"{BASIC_SCOPE},{PROFILE_SCOPE}")
    assert "username" in profile
    assert "bio_description" in profile
    assert "profile_deep_link" in profile
    assert "is_verified" in profile
    assert "follower_count" not in profile

    stats = user_info_fields(f"{BASIC_SCOPE},{STATS_SCOPE}")
    assert "follower_count" in stats
    assert "following_count" in stats
    assert "likes_count" in stats
    assert "video_count" in stats
    assert "username" not in stats
