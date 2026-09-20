import logging

from fastapi import APIRouter, HTTPException, status
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import get_settings
from app.db.session import engine

router = APIRouter(tags=["system"])
logger = logging.getLogger("readiness")


@router.get("/health")
def health():
    return {"status": "ok", "service": "th-tiktok-manager-api"}


@router.get("/ready")
def ready():
    settings = get_settings()
    checks = {"database": False, "cache": False}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except SQLAlchemyError as exc:
        logger.warning("Database readiness failed: %s", type(exc).__name__)


    try:
        with Redis.from_url(settings.cache_url, socket_timeout=1) as cache:
            cache.ping()
        checks["cache"] = True
    except RedisError as exc:
        logger.warning("Cache readiness failed: %s", type(exc).__name__)

    if not all(checks.values()):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": checks},
        )
    return {"status": "ready", "checks": checks}
