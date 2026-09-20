import json
from datetime import UTC, datetime, timedelta
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import and_, or_, select

from app.api.auth import DbSession, require_admin
from app.models.admin_session import AdminSession
from app.models.media_asset import MediaAsset
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_draft_job import TikTokDraftJob
from app.models.tiktok_publish_job import TikTokPublishJob
from app.schemas.publishing import (
    CreatorInfoSummary,
    DirectPhotoPostRequest,
    DirectVideoPostRequest,
    DraftJobSummary,
    MediaAssetSummary,
    PhotoDraftCreateRequest,
    PublishJobSummary,
    PublishRescheduleRequest,
    PublishScheduleSummary,
    VideoDraftCreateRequest,
)
from app.services.audit import record_audit
from app.services.media_library import MediaValidationError, asset_path, save_video_upload
from app.services.tiktok.client import TikTokAPIError
from app.services.tiktok.direct_posts import (
    DirectPostOptions,
    TikTokPublishScopeError,
    TikTokPublishValidationError,
    creator_info_json,
    fetch_publish_status,
    query_creator_info,
    require_publish_scope,
    validate_direct_post,
)
from app.services.tiktok.drafts import (
    TikTokDraftScopeError,
    TikTokDraftValidationError,
    encode_photo_source,
    fetch_draft_status,
    require_upload_scope,
    validate_photo_request,
)

router = APIRouter(prefix="/tiktok", tags=["publishing"])
Admin = Annotated[AdminSession, Depends(require_admin)]


def _asset_summary(asset: MediaAsset) -> MediaAssetSummary:
    return MediaAssetSummary(
        id=asset.id,
        kind=asset.kind,
        original_name=asset.original_name,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
        sha256=asset.sha256,
        duration_seconds=asset.duration_seconds,
        created_at=asset.created_at,
    )


def _job_summary(job: TikTokDraftJob) -> DraftJobSummary:
    try:
        public_ids = json.loads(job.public_post_ids) if job.public_post_ids else []
    except json.JSONDecodeError:
        public_ids = []
    return DraftJobSummary(
        id=job.id,
        account_id=job.account_id,
        media_asset_id=job.media_asset_id,
        media_type=job.media_type,
        source_type=job.source_type,
        title=job.title,
        description=job.description,
        publish_id=job.publish_id,
        status=job.status,
        fail_reason=job.fail_reason,
        uploaded_bytes=job.uploaded_bytes,
        downloaded_bytes=job.downloaded_bytes,
        public_post_ids=[str(value) for value in public_ids],
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _publish_summary(job: TikTokPublishJob) -> PublishJobSummary:
    try:
        public_ids = json.loads(job.public_post_ids) if job.public_post_ids else []
    except json.JSONDecodeError:
        public_ids = []
    return PublishJobSummary(
        id=job.id,
        account_id=job.account_id,
        media_asset_id=job.media_asset_id,
        media_type=job.media_type,
        source_type=job.source_type,
        title=job.title,
        description=job.description,
        privacy_level=job.privacy_level,
        disable_comment=job.disable_comment,
        disable_duet=job.disable_duet,
        disable_stitch=job.disable_stitch,
        auto_add_music=job.auto_add_music,
        brand_content_toggle=job.brand_content_toggle,
        brand_organic_toggle=job.brand_organic_toggle,
        is_aigc=job.is_aigc,
        video_cover_timestamp_ms=job.video_cover_timestamp_ms,
        publish_id=job.publish_id,
        status=job.status,
        fail_reason=job.fail_reason,
        uploaded_bytes=job.uploaded_bytes,
        downloaded_bytes=job.downloaded_bytes,
        public_post_ids=[str(value) for value in public_ids],
        scheduled_at=job.scheduled_at,
        schedule_status=job.schedule_status,
        retry_count=job.retry_count,
        max_retries=job.max_retries,
        next_attempt_at=job.next_attempt_at,
        last_attempt_at=job.last_attempt_at,
        canceled_at=job.canceled_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _schedule_values(
    scheduled_at: datetime | None,
) -> tuple[datetime | None, str]:
    if scheduled_at is None:
        return None, "READY"
    if scheduled_at.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="scheduled_at must include a timezone offset",
        )
    value = scheduled_at.astimezone(UTC)
    if value <= datetime.now(UTC) + timedelta(seconds=30):
        raise HTTPException(
            status_code=400,
            detail="Scheduled publish time must be at least 30 seconds in the future",
        )
    return value, "SCHEDULED"


def _connected_publish_account(db: DbSession, account_id: int) -> TikTokAccount:
    account = db.get(TikTokAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="TikTok account not found")
    if account.status != "CONNECTED":
        raise HTTPException(status_code=409, detail="TikTok account is not connected")
    try:
        require_publish_scope(account)
    except TikTokPublishScopeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return account


def _connected_account(db: DbSession, account_id: int) -> TikTokAccount:
    account = db.get(TikTokAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="TikTok account not found")
    if account.status != "CONNECTED":
        raise HTTPException(status_code=409, detail="TikTok account is not connected")
    try:
        require_upload_scope(account)
    except TikTokDraftScopeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return account


@router.get("/media", response_model=list[MediaAssetSummary])
def list_media(
    _: Admin,
    db: DbSession,
    limit: int = Query(default=100, ge=1, le=500),
):
    rows = db.scalars(
        select(MediaAsset).order_by(MediaAsset.id.desc()).limit(limit)
    ).all()
    return [_asset_summary(row) for row in rows]


@router.get("/media/{asset_id}/content")
def media_content(asset_id: int, _: Admin, db: DbSession):
    asset = db.get(MediaAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Media asset not found")
    try:
        path = asset_path(asset)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path, media_type=asset.mime_type)


@router.post("/media/video", response_model=MediaAssetSummary)
async def upload_video_media(
    _: Admin,
    db: DbSession,
    file: Annotated[UploadFile, File()],
    duration_seconds: Annotated[float | None, Form()] = None,
):
    try:
        asset = await save_video_upload(
            db, file, duration_seconds=duration_seconds
        )
    except MediaValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    record_audit(
        db,
        event_type="MEDIA_UPLOADED",
        detail=f"Stored video media asset id={asset.id} size={asset.size_bytes}",
    )
    return _asset_summary(asset)


@router.get("/drafts", response_model=list[DraftJobSummary])
def list_drafts(
    _: Admin,
    db: DbSession,
    account_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    query = select(TikTokDraftJob)
    if account_id is not None:
        query = query.where(TikTokDraftJob.account_id == account_id)
    rows = db.scalars(query.order_by(TikTokDraftJob.id.desc()).limit(limit)).all()
    return [_job_summary(row) for row in rows]


@router.post(
    "/accounts/{account_id}/drafts/video",
    response_model=DraftJobSummary,
)
def create_video_draft(
    account_id: int,
    payload: VideoDraftCreateRequest,
    _: Admin,
    db: DbSession,
):
    account = _connected_account(db, account_id)
    asset = db.get(MediaAsset, payload.media_asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Media asset not found")
    if asset.kind != "VIDEO":
        raise HTTPException(status_code=400, detail="Selected media asset is not a video")

    now = datetime.now(UTC)
    job = TikTokDraftJob(
        account_id=account.id,
        media_asset_id=asset.id,
        media_type="VIDEO",
        source_type="FILE_UPLOAD",
        status="QUEUED",
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    record_audit(
        db,
        event_type="DRAFT_QUEUED",
        account_id=account.id,
        detail=f"Queued video draft job id={job.id}",
    )
    return _job_summary(job)


@router.post(
    "/accounts/{account_id}/drafts/photo",
    response_model=DraftJobSummary,
)
def create_photo_draft(
    account_id: int,
    payload: PhotoDraftCreateRequest,
    _: Admin,
    db: DbSession,
):
    account = _connected_account(db, account_id)
    try:
        validate_photo_request(
            photo_urls=payload.photo_urls,
            cover_index=payload.cover_index,
            title=payload.title,
            description=payload.description,
        )
    except TikTokDraftValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    now = datetime.now(UTC)
    job = TikTokDraftJob(
        account_id=account.id,
        media_type="PHOTO",
        source_type="PULL_FROM_URL",
        source_json=encode_photo_source(
            payload.photo_urls,
            payload.cover_index,
            payload.is_aigc,
        ),
        title=payload.title,
        description=payload.description,
        status="QUEUED",
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    record_audit(
        db,
        event_type="DRAFT_QUEUED",
        account_id=account.id,
        detail=f"Queued photo draft job id={job.id}",
    )
    return _job_summary(job)


@router.post("/drafts/{job_id}/refresh", response_model=DraftJobSummary)
def refresh_draft_status(
    job_id: int,
    _: Admin,
    db: DbSession,
):
    job = db.get(TikTokDraftJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Draft job not found")
    if not job.publish_id:
        raise HTTPException(status_code=409, detail="Draft has not been submitted to TikTok yet")
    account = _connected_account(db, job.account_id)

    try:
        remote = fetch_draft_status(account, job.publish_id)
    except TikTokAPIError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="TikTok status endpoint unavailable") from exc

    job.status = remote.status
    job.fail_reason = remote.fail_reason
    job.uploaded_bytes = remote.uploaded_bytes
    job.downloaded_bytes = remote.downloaded_bytes
    job.public_post_ids = json.dumps(remote.public_post_ids)
    job.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(job)
    return _job_summary(job)


@router.post(
    "/accounts/{account_id}/creator-info",
    response_model=CreatorInfoSummary,
)
def creator_info(account_id: int, _: Admin, db: DbSession):
    account = _connected_publish_account(db, account_id)
    try:
        info = query_creator_info(account)
    except TikTokAPIError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="TikTok creator-info endpoint unavailable") from exc

    return CreatorInfoSummary(
        creator_avatar_url=info.creator_avatar_url,
        creator_username=info.creator_username,
        creator_nickname=info.creator_nickname,
        privacy_level_options=info.privacy_level_options,
        comment_disabled=info.comment_disabled,
        duet_disabled=info.duet_disabled,
        stitch_disabled=info.stitch_disabled,
        max_video_post_duration_sec=info.max_video_post_duration_sec,
    )


@router.get("/publish-jobs", response_model=list[PublishJobSummary])
def list_publish_jobs(
    _: Admin,
    db: DbSession,
    account_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    query = select(TikTokPublishJob)
    if account_id is not None:
        query = query.where(TikTokPublishJob.account_id == account_id)
    rows = db.scalars(query.order_by(TikTokPublishJob.id.desc()).limit(limit)).all()
    return [_publish_summary(row) for row in rows]


@router.post(
    "/accounts/{account_id}/publish/video",
    response_model=PublishJobSummary,
)
def create_video_publish_job(
    account_id: int,
    payload: DirectVideoPostRequest,
    _: Admin,
    db: DbSession,
):
    account = _connected_publish_account(db, account_id)
    asset = db.get(MediaAsset, payload.media_asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Media asset not found")
    if asset.kind != "VIDEO":
        raise HTTPException(status_code=400, detail="Selected media asset is not a video")

    scheduled_at, schedule_status = _schedule_values(payload.scheduled_at)

    try:
        info = query_creator_info(account)
        options = DirectPostOptions(
            privacy_level=payload.privacy_level,
            allow_comment=payload.allow_comment,
            allow_duet=payload.allow_duet,
            allow_stitch=payload.allow_stitch,
            brand_content_toggle=payload.brand_content_toggle,
            brand_organic_toggle=payload.brand_organic_toggle,
            is_aigc=payload.is_aigc,
            consent_music_usage=payload.consent_music_usage,
            consent_branded_policy=payload.consent_branded_policy,
            title=payload.title,
            video_cover_timestamp_ms=payload.video_cover_timestamp_ms,
        )
        validate_direct_post(
            info=info,
            media_type="VIDEO",
            options=options,
            asset=asset,
        )
    except (TikTokAPIError, TikTokPublishValidationError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="TikTok creator-info endpoint unavailable") from exc

    now = datetime.now(UTC)
    job = TikTokPublishJob(
        account_id=account.id,
        media_asset_id=asset.id,
        media_type="VIDEO",
        source_type="FILE_UPLOAD",
        title=payload.title,
        privacy_level=payload.privacy_level,
        disable_comment=not payload.allow_comment,
        disable_duet=not payload.allow_duet,
        disable_stitch=not payload.allow_stitch,
        auto_add_music=False,
        brand_content_toggle=payload.brand_content_toggle,
        brand_organic_toggle=payload.brand_organic_toggle,
        is_aigc=payload.is_aigc,
        video_cover_timestamp_ms=payload.video_cover_timestamp_ms,
        consent_music_usage=payload.consent_music_usage,
        consent_branded_policy=payload.consent_branded_policy,
        creator_info_json=creator_info_json(info),
        status="QUEUED",
        scheduled_at=scheduled_at,
        schedule_status=schedule_status,
        retry_count=0,
        max_retries=payload.max_retries,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    record_audit(
        db,
        event_type="DIRECT_POST_QUEUED",
        account_id=account.id,
        detail=f"Direct Post video job id={job.id} schedule_status={job.schedule_status}",
    )
    return _publish_summary(job)


@router.post(
    "/accounts/{account_id}/publish/photo",
    response_model=PublishJobSummary,
)
def create_photo_publish_job(
    account_id: int,
    payload: DirectPhotoPostRequest,
    _: Admin,
    db: DbSession,
):
    account = _connected_publish_account(db, account_id)
    scheduled_at, schedule_status = _schedule_values(payload.scheduled_at)
    try:
        info = query_creator_info(account)
        options = DirectPostOptions(
            privacy_level=payload.privacy_level,
            allow_comment=payload.allow_comment,
            allow_duet=False,
            allow_stitch=False,
            brand_content_toggle=payload.brand_content_toggle,
            brand_organic_toggle=payload.brand_organic_toggle,
            is_aigc=payload.is_aigc,
            consent_music_usage=payload.consent_music_usage,
            consent_branded_policy=payload.consent_branded_policy,
            title=payload.title,
            description=payload.description,
            auto_add_music=payload.auto_add_music,
        )
        validate_direct_post(
            info=info,
            media_type="PHOTO",
            options=options,
            photo_urls=payload.photo_urls,
            cover_index=payload.cover_index,
        )
    except (TikTokAPIError, TikTokPublishValidationError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="TikTok creator-info endpoint unavailable") from exc

    source_json = json.dumps(
        {
            "photo_urls": payload.photo_urls,
            "cover_index": payload.cover_index,
        },
        separators=(",", ":"),
    )
    now = datetime.now(UTC)
    job = TikTokPublishJob(
        account_id=account.id,
        media_type="PHOTO",
        source_type="PULL_FROM_URL",
        source_json=source_json,
        title=payload.title,
        description=payload.description,
        privacy_level=payload.privacy_level,
        disable_comment=not payload.allow_comment,
        disable_duet=True,
        disable_stitch=True,
        auto_add_music=payload.auto_add_music,
        brand_content_toggle=payload.brand_content_toggle,
        brand_organic_toggle=payload.brand_organic_toggle,
        is_aigc=payload.is_aigc,
        consent_music_usage=payload.consent_music_usage,
        consent_branded_policy=payload.consent_branded_policy,
        creator_info_json=creator_info_json(info),
        status="QUEUED",
        scheduled_at=scheduled_at,
        schedule_status=schedule_status,
        retry_count=0,
        max_retries=payload.max_retries,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    record_audit(
        db,
        event_type="DIRECT_POST_QUEUED",
        account_id=account.id,
        detail=f"Direct Post photo job id={job.id} schedule_status={job.schedule_status}",
    )
    return _publish_summary(job)


@router.get("/publish-schedule", response_model=PublishScheduleSummary)
def publish_schedule(
    _: Admin,
    db: DbSession,
    days: int = Query(default=7),
    account_id: int | None = Query(default=None),
):
    if days not in {7, 30}:
        raise HTTPException(status_code=400, detail="Schedule range must be 7 or 30 days")
    now = datetime.now(UTC)
    end = now + timedelta(days=days)
    window_start = now - timedelta(days=1)
    query = select(TikTokPublishJob).where(
        or_(
            and_(
                TikTokPublishJob.scheduled_at.is_not(None),
                TikTokPublishJob.scheduled_at >= window_start,
                TikTokPublishJob.scheduled_at <= end,
            ),
            and_(
                TikTokPublishJob.next_attempt_at.is_not(None),
                TikTokPublishJob.next_attempt_at >= window_start,
                TikTokPublishJob.next_attempt_at <= end,
            ),
        )
    )
    if account_id is not None:
        query = query.where(TikTokPublishJob.account_id == account_id)
    rows = db.scalars(
        query.order_by(
            TikTokPublishJob.next_attempt_at.asc().nulls_last(),
            TikTokPublishJob.scheduled_at.asc().nulls_last(),
            TikTokPublishJob.id.asc(),
        )
    ).all()
    counts = {
        "SCHEDULED": 0,
        "READY": 0,
        "RUNNING": 0,
        "COMPLETED": 0,
        "FAILED": 0,
        "CANCELED": 0,
    }
    for row in rows:
        if row.schedule_status in counts:
            counts[row.schedule_status] += 1
    return PublishScheduleSummary(
        days=days,
        total=len(rows),
        scheduled=counts["SCHEDULED"],
        ready=counts["READY"],
        running=counts["RUNNING"],
        completed=counts["COMPLETED"],
        failed=counts["FAILED"],
        canceled=counts["CANCELED"],
        jobs=[_publish_summary(row) for row in rows],
    )


@router.post("/publish-jobs/{job_id}/cancel", response_model=PublishJobSummary)
def cancel_publish_job(job_id: int, _: Admin, db: DbSession):
    job = db.get(TikTokPublishJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Publish job not found")
    if job.publish_id is not None:
        raise HTTPException(
            status_code=409,
            detail="A post already submitted to TikTok cannot be canceled locally",
        )
    if job.schedule_status not in {"SCHEDULED", "READY"}:
        raise HTTPException(status_code=409, detail="Publish job cannot be canceled now")

    now = datetime.now(UTC)
    job.status = "CANCELED"
    job.schedule_status = "CANCELED"
    job.canceled_at = now
    job.updated_at = now
    db.commit()
    db.refresh(job)
    record_audit(
        db,
        event_type="DIRECT_POST_CANCELED",
        account_id=job.account_id,
        detail=f"Canceled Direct Post job id={job.id}",
    )
    return _publish_summary(job)


@router.post(
    "/publish-jobs/{job_id}/reschedule",
    response_model=PublishJobSummary,
)
def reschedule_publish_job(
    job_id: int,
    payload: PublishRescheduleRequest,
    _: Admin,
    db: DbSession,
):
    job = db.get(TikTokPublishJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Publish job not found")
    if job.publish_id is not None:
        raise HTTPException(
            status_code=409,
            detail="A post already submitted to TikTok cannot be rescheduled",
        )
    if job.schedule_status not in {"SCHEDULED", "READY"}:
        raise HTTPException(status_code=409, detail="Publish job cannot be rescheduled now")

    scheduled_at, _ = _schedule_values(payload.scheduled_at)
    now = datetime.now(UTC)
    job.status = "QUEUED"
    job.schedule_status = "SCHEDULED"
    job.scheduled_at = scheduled_at
    job.next_attempt_at = None
    job.canceled_at = None
    job.fail_reason = None
    job.updated_at = now
    db.commit()
    db.refresh(job)
    record_audit(
        db,
        event_type="DIRECT_POST_RESCHEDULED",
        account_id=job.account_id,
        detail=f"Rescheduled Direct Post job id={job.id} for {scheduled_at.isoformat()}",
    )
    return _publish_summary(job)


@router.post("/publish-jobs/{job_id}/retry", response_model=PublishJobSummary)
def retry_publish_job(job_id: int, _: Admin, db: DbSession):
    job = db.get(TikTokPublishJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Publish job not found")
    if job.publish_id is not None:
        raise HTTPException(
            status_code=409,
            detail="A submitted TikTok post cannot be re-initialized",
        )
    if job.schedule_status != "FAILED" or job.status != "FAILED":
        raise HTTPException(status_code=409, detail="Only failed pre-submit jobs can be retried")
    if job.retry_count >= job.max_retries:
        raise HTTPException(status_code=409, detail="Publish retry limit has been reached")

    now = datetime.now(UTC)
    job.retry_count += 1
    job.status = "QUEUED"
    job.schedule_status = "READY"
    job.next_attempt_at = None
    job.fail_reason = None
    job.updated_at = now
    db.commit()
    db.refresh(job)
    record_audit(
        db,
        event_type="DIRECT_POST_MANUAL_RETRY",
        account_id=job.account_id,
        detail=f"Manual retry for Direct Post job id={job.id} retry={job.retry_count}",
    )
    return _publish_summary(job)


@router.post("/publish-jobs/{job_id}/refresh", response_model=PublishJobSummary)
def refresh_publish_job(
    job_id: int,
    _: Admin,
    db: DbSession,
):
    job = db.get(TikTokPublishJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Publish job not found")
    if not job.publish_id:
        raise HTTPException(status_code=409, detail="Post has not been submitted to TikTok yet")
    account = _connected_publish_account(db, job.account_id)

    try:
        remote = fetch_publish_status(account, job.publish_id)
    except TikTokAPIError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="TikTok status endpoint unavailable") from exc

    job.status = remote.status
    job.fail_reason = remote.fail_reason
    job.uploaded_bytes = remote.uploaded_bytes or job.uploaded_bytes
    job.downloaded_bytes = remote.downloaded_bytes
    job.public_post_ids = json.dumps(remote.public_post_ids)
    job.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(job)
    return _publish_summary(job)
