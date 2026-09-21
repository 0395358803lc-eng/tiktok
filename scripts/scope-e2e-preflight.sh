#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export TIKTOK_SCOPES="user.info.basic,user.info.profile,user.info.stats,video.list,video.upload,video.publish"
cd "$ROOT/backend"

"$ROOT/.venv/bin/python" - <<'PY'
from app.core.settings import get_settings
from app.services.tiktok.scopes import (
    PERSONAL_SCOPES,
    configured_personal_scopes,
    validate_requested_scopes,
)

settings = get_settings()
configured = configured_personal_scopes(settings)
print("TikTok scope preflight")
print("environment:", settings.tiktok_environment)
print("configured:", ",".join(configured) or "(none)")
print()

blocked = 0
for scope in PERSONAL_SCOPES:
    requested = ["user.info.basic"] if scope == "user.info.basic" else ["user.info.basic", scope]
    try:
        accepted = validate_requested_scopes(requested, settings)
        print(f"PASS    {scope:<20} OAuth requestable: {','.join(accepted)}")
    except ValueError as exc:
        blocked += 1
        print(f"BLOCKED {scope:<20} {exc}")

print()
print(f"summary: configured={len(configured)} supported={len(PERSONAL_SCOPES)} blocked={blocked}")
PY
