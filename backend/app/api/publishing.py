import json
from datetime import UTC, datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select

from app.api.auth import DbSession, require_admin
from app.models.admin_session import AdminSession
from app.models.media_asset import MediaAsset
from app.models.tiktok_account import TikTokAccount
from app.models.tiktok_draft_job import TikTokDraftJob
from app.schemas.publishing import (
    DraftJobSummary,
    MediaAssetSummary,
    PhotoDraftCreateRequest,
    VideoDraftCreateRequest,
)
from app.services.audit import record_audit
from app.services.media_library import MediaValidationError, save_video_upload
from app.services.tiktok.client import TikTokAPIError
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


@router.post("/media/video", response_model=MediaAssetSummary)
async def upload_video_media(
    _: Admin,
    db: DbSession,
    file: Annotated[UploadFile, File()],
):
    try:
        asset = await save_video_upload(db, file)
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
