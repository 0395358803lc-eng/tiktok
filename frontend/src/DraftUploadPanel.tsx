import { FormEvent, useEffect, useMemo, useState } from "react";

import { api, DraftJob, MediaAsset, TikTokAccount } from "./api";
import { readVideoDuration } from "./media";

type Props = {
  accounts: TikTokAccount[];
};

export default function DraftUploadPanel({ accounts }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(accounts[0]?.id ?? null);
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [jobs, setJobs] = useState<DraftJob[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const selected = useMemo(
    () => accounts.find((account) => account.id === selectedId) ?? null,
    [accounts, selectedId],
  );
  const hasUploadScope = Boolean(selected?.scopes.includes("video.upload"));

  useEffect(() => {
    if (selectedId === null && accounts.length > 0) {
      setSelectedId(accounts[0].id);
    } else if (selectedId !== null && !accounts.some((account) => account.id === selectedId)) {
      setSelectedId(accounts[0]?.id ?? null);
    }
  }, [accounts, selectedId]);

  useEffect(() => {
    void loadAssets();
  }, []);

  useEffect(() => {
    if (selectedId !== null) void loadJobs(selectedId);
    else setJobs([]);
  }, [selectedId]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (selectedId !== null) void loadJobs(selectedId);
    }, 15000);
    return () => window.clearInterval(timer);
  }, [selectedId]);

  async function loadAssets() {
    try {
      const rows = await api.mediaAssets();
      setAssets(rows.filter((asset) => asset.kind === "VIDEO"));
      if (selectedAsset === null && rows.length > 0) {
        const firstVideo = rows.find((asset) => asset.kind === "VIDEO");
        if (firstVideo) setSelectedAsset(firstVideo.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load media library");
    }
  }

  async function loadJobs(accountId: number) {
    try {
      setJobs(await api.draftJobs(accountId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load draft jobs");
    }
  }

  async function uploadVideo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const file = data.get("video");
    if (!(file instanceof File) || file.size === 0) {
      setError("Choose an MP4, MOV, or WebM video first.");
      return;
    }

    setBusy(true);
    setError("");
    setNotice("");
    try {
      const duration = await readVideoDuration(file);
      const asset = await api.uploadVideoMedia(file, duration);
      await loadAssets();
      setSelectedAsset(asset.id);
      form.reset();
      setNotice("Video stored in Media Library. It has not been sent to TikTok yet.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Video upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function queueVideo() {
    if (!selected || selectedAsset === null) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const job = await api.createVideoDraft(selected.id, selectedAsset);
      await loadJobs(selected.id);
      setNotice("Draft job #" + job.id + " queued. DraftWorker will send it to TikTok.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to queue video draft");
    } finally {
      setBusy(false);
    }
  }

  async function queuePhotos(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const urls = String(data.get("photo_urls") ?? "")
      .split(/\r?\n/)
      .map((url) => url.trim())
      .filter(Boolean);
    const title = String(data.get("title") ?? "").trim();
    const description = String(data.get("description") ?? "").trim();
    const coverIndex = Number(data.get("cover_index") ?? 0);
    const isAigc = data.get("is_aigc") === "on";

    setBusy(true);
    setError("");
    setNotice("");
    try {
      const job = await api.createPhotoDraft(selected.id, {
        photo_urls: urls,
        cover_index: coverIndex,
        title: title || undefined,
        description: description || undefined,
        is_aigc: isAigc,
      });
      await loadJobs(selected.id);
      setNotice("Photo draft job #" + job.id + " queued for TikTok Inbox.");
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to queue photo draft");
    } finally {
      setBusy(false);
    }
  }

  async function refreshJob(jobId: number) {
    setBusy(true);
    setError("");
    try {
      await api.refreshDraft(jobId);
      if (selectedId !== null) await loadJobs(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to refresh draft status");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel draft-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">CONTENT POSTING API · VIDEO.UPLOAD</span>
          <h3>Draft Upload Studio</h3>
        </div>
        {accounts.length > 0 && (
          <select
            className="video-account-select"
            value={selectedId ?? ""}
            onChange={(event) => {
              setSelectedId(Number(event.target.value));
              setError("");
              setNotice("");
            }}
          >
            {accounts.map((account) => (
              <option value={account.id} key={account.id}>
                {account.display_name || account.username || "Account #" + account.id}
              </option>
            ))}
          </select>
        )}
      </div>

      {!selected ? (
        <div className="empty-state">
          <strong>No connected account.</strong>
          <span>Connect a TikTok account before creating drafts.</span>
        </div>
      ) : !hasUploadScope ? (
        <div className="setup-box">
          <strong>video.upload permission required</strong>
          <p>
            Enable Content Posting API + <code>video.upload</code> in TikTok Developer Portal,
            add the scope to this app, then reconnect the account. Media can still be staged
            locally before that permission is granted.
          </p>
        </div>
      ) : null}

      {error && <div className="error global-error">{error}</div>}
      {notice && <div className="notice">{notice}</div>}

      <div className="draft-studio-grid">
        <article className="draft-card">
          <span className="eyebrow">VIDEO DRAFT</span>
          <h4>Local Media Library</h4>
          <form className="draft-form" onSubmit={uploadVideo}>
            <label>
              MP4, MOV, or WebM
              <input
                name="video"
                type="file"
                accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm"
                disabled={busy}
              />
            </label>
            <button type="submit" className="ghost" disabled={busy}>
              {busy ? "Working…" : "Store video"}
            </button>
          </form>

          <label>
            Stored video
            <select
              value={selectedAsset ?? ""}
              onChange={(event) => setSelectedAsset(Number(event.target.value))}
              disabled={assets.length === 0}
            >
              {assets.length === 0 && <option value="">No videos stored</option>}
              {assets.map((asset) => (
                <option value={asset.id} key={asset.id}>
                  {asset.original_name} · {formatBytes(asset.size_bytes)}
                </option>
              ))}
            </select>
          </label>
          <button
            disabled={busy || !hasUploadScope || selectedAsset === null}
            onClick={queueVideo}
          >
            Queue video to TikTok Draft
          </button>
          <p className="draft-help">
            TikTok sends the uploaded video to the creator's Inbox. The creator must open
            TikTok to edit and complete the post.
          </p>
        </article>

        <article className="draft-card">
          <span className="eyebrow">PHOTO DRAFT</span>
          <h4>Verified HTTPS image URLs</h4>
          <form className="draft-form" onSubmit={queuePhotos}>
            <label>
              Photo URLs · one per line · max 35
              <textarea
                name="photo_urls"
                rows={5}
                placeholder={"https://verified.example/photo-1.jpg\nhttps://verified.example/photo-2.webp"}
                disabled={busy}
              />
            </label>
            <div className="draft-inline">
              <label>
                Cover index
                <input name="cover_index" type="number" min="0" defaultValue="0" />
              </label>
              <label className="check-label">
                <input name="is_aigc" type="checkbox" />
                AI-generated
              </label>
            </div>
            <label>
              Title
              <input name="title" maxLength={90} />
            </label>
            <label>
              Description
              <textarea name="description" rows={3} maxLength={4000} />
            </label>
            <button type="submit" disabled={busy || !hasUploadScope}>
              Queue photo draft
            </button>
          </form>
        </article>
      </div>

      <div className="draft-jobs-head">
        <div>
          <strong>Draft jobs</strong>
          <span>Auto-refreshes every 15 seconds</span>
        </div>
        <button
          className="ghost"
          disabled={busy || selectedId === null}
          onClick={() => selectedId !== null && loadJobs(selectedId)}
        >
          Refresh list
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="empty-state">
          <strong>No draft jobs for this account.</strong>
          <span>Queue a video or photo draft to begin.</span>
        </div>
      ) : (
        <div className="draft-job-list">
          {jobs.map((job) => (
            <article className="draft-job" key={job.id}>
              <div>
                <strong>#{job.id} · {job.media_type}</strong>
                <span>{new Date(job.created_at).toLocaleString()}</span>
                {job.publish_id && <span>Publish ID: {job.publish_id}</span>}
                {job.fail_reason && <span className="draft-failure">{job.fail_reason}</span>}
                {job.status === "SEND_TO_USER_INBOX" && (
                  <span className="draft-inbox">
                    TikTok Inbox notification delivered — open TikTok to finish editing/posting.
                  </span>
                )}
              </div>
              <div className="draft-job-actions">
                <span className={"draft-status status-" + job.status.toLowerCase()}>
                  {job.status}
                </span>
                {job.publish_id && !["FAILED", "PUBLISH_COMPLETE"].includes(job.status) && (
                  <button className="ghost" disabled={busy} onClick={() => refreshJob(job.id)}>
                    Check status
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function formatBytes(value: number) {
  if (value < 1024 * 1024) return (value / 1024).toFixed(1) + " KB";
  if (value < 1024 * 1024 * 1024) return (value / 1024 / 1024).toFixed(1) + " MB";
  return (value / 1024 / 1024 / 1024).toFixed(2) + " GB";
}
