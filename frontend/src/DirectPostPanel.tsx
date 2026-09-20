import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  api,
  CreatorInfo,
  MediaAsset,
  PublishJob,
  TikTokAccount,
} from "./api";
import { readVideoDuration } from "./media";

type Props = {
  accounts: TikTokAccount[];
};

type Mode = "VIDEO" | "PHOTO";

export default function DirectPostPanel({ accounts }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(accounts[0]?.id ?? null);
  const [mode, setMode] = useState<Mode>("VIDEO");
  const [creator, setCreator] = useState<CreatorInfo | null>(null);
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null);
  const [jobs, setJobs] = useState<PublishJob[]>([]);
  const [privacy, setPrivacy] = useState("");
  const [allowComment, setAllowComment] = useState(false);
  const [allowDuet, setAllowDuet] = useState(false);
  const [allowStitch, setAllowStitch] = useState(false);
  const [commercial, setCommercial] = useState(false);
  const [yourBrand, setYourBrand] = useState(false);
  const [brandedContent, setBrandedContent] = useState(false);
  const [isAigc, setIsAigc] = useState(false);
  const [autoAddMusic, setAutoAddMusic] = useState(false);
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [title, setTitle] = useState("");
  const [photoDescription, setPhotoDescription] = useState("");
  const [photoUrls, setPhotoUrls] = useState("");
  const [photoCoverIndex, setPhotoCoverIndex] = useState(0);
  const [coverSeconds, setCoverSeconds] = useState("");
  const [busy, setBusy] = useState(false);
  const [creatorBusy, setCreatorBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const selected = useMemo(
    () => accounts.find((account) => account.id === selectedId) ?? null,
    [accounts, selectedId],
  );
  const selectedMedia = useMemo(
    () => assets.find((asset) => asset.id === selectedAsset) ?? null,
    [assets, selectedAsset],
  );
  const hasPublishScope = Boolean(selected?.scopes.includes("video.publish"));

  const parsedPhotoUrls = useMemo(
    () =>
      photoUrls
        .split(/\r?\n/)
        .map((url) => url.trim())
        .filter(Boolean),
    [photoUrls],
  );

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
    resetPostChoices();
    setCreator(null);
    if (selectedId !== null) {
      void loadJobs(selectedId);
      if (accounts.find((account) => account.id === selectedId)?.scopes.includes("video.publish")) {
        void loadCreator(selectedId);
      }
    } else {
      setJobs([]);
    }
  }, [selectedId]);

  useEffect(() => {
    setConsentAccepted(false);
    if (!commercial) {
      setYourBrand(false);
      setBrandedContent(false);
    }
  }, [commercial, brandedContent]);

  useEffect(() => {
    if (brandedContent && privacy === "SELF_ONLY") {
      setPrivacy("");
    }
  }, [brandedContent, privacy]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (selectedId !== null) void loadJobs(selectedId);
    }, 15000);
    return () => window.clearInterval(timer);
  }, [selectedId]);

  function resetPostChoices() {
    setPrivacy("");
    setAllowComment(false);
    setAllowDuet(false);
    setAllowStitch(false);
    setCommercial(false);
    setYourBrand(false);
    setBrandedContent(false);
    setIsAigc(false);
    setAutoAddMusic(false);
    setConsentAccepted(false);
    setTitle("");
    setPhotoDescription("");
    setCoverSeconds("");
  }

  async function loadCreator(accountId: number) {
    setCreatorBusy(true);
    setError("");
    try {
      const info = await api.creatorInfo(accountId);
      setCreator(info);
      setPrivacy("");
      setAllowComment(false);
      setAllowDuet(false);
      setAllowStitch(false);
      setConsentAccepted(false);
    } catch (err) {
      setCreator(null);
      setError(err instanceof Error ? err.message : "Unable to load Creator Info");
    } finally {
      setCreatorBusy(false);
    }
  }

  async function loadAssets() {
    try {
      const rows = (await api.mediaAssets()).filter((asset) => asset.kind === "VIDEO");
      setAssets(rows);
      if (selectedAsset === null && rows.length > 0) setSelectedAsset(rows[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load Media Library");
    }
  }

  async function loadJobs(accountId: number) {
    try {
      setJobs(await api.publishJobs(accountId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load Direct Post jobs");
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
      if (
        creator?.max_video_post_duration_sec &&
        duration > creator.max_video_post_duration_sec
      ) {
        throw new Error(
          "This video is longer than the current creator limit of " +
            creator.max_video_post_duration_sec +
            " seconds.",
        );
      }
      const asset = await api.uploadVideoMedia(file, duration);
      await loadAssets();
      setSelectedAsset(asset.id);
      form.reset();
      setNotice(
        "Video stored with duration metadata. Review the preview and settings before posting.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Video upload failed");
    } finally {
      setBusy(false);
    }
  }

  function validateCommon(): string | null {
    if (!creator) return "Load Creator Info before posting.";
    if (!privacy) return "Choose a privacy setting.";
    if (!consentAccepted) return "Accept the required TikTok posting declaration.";
    if (commercial && !yourBrand && !brandedContent) {
      return "Choose Your brand, Branded content, or both.";
    }
    if (brandedContent && privacy === "SELF_ONLY") {
      return "Branded content cannot use Only me visibility.";
    }
    return null;
  }

  async function queueVideo() {
    if (!selected || selectedAsset === null) return;
    const commonError = validateCommon();
    if (commonError) {
      setError(commonError);
      return;
    }
    if (!selectedMedia?.duration_seconds) {
      setError("This stored video has no duration metadata. Upload it again before Direct Post.");
      return;
    }
    if (
      creator?.max_video_post_duration_sec &&
      selectedMedia.duration_seconds > creator.max_video_post_duration_sec
    ) {
      setError("Selected video exceeds the creator's current maximum duration.");
      return;
    }

    const seconds = coverSeconds.trim() ? Number(coverSeconds) : undefined;
    if (seconds !== undefined && (!Number.isFinite(seconds) || seconds < 0)) {
      setError("Cover frame must be a non-negative number of seconds.");
      return;
    }

    setBusy(true);
    setError("");
    setNotice("");
    try {
      const job = await api.createVideoPublish(selected.id, {
        media_asset_id: selectedAsset,
        privacy_level: privacy,
        title: title.trim() || undefined,
        allow_comment: allowComment,
        allow_duet: allowDuet,
        allow_stitch: allowStitch,
        brand_content_toggle: commercial && brandedContent,
        brand_organic_toggle: commercial && yourBrand,
        is_aigc: isAigc,
        video_cover_timestamp_ms:
          seconds === undefined ? undefined : Math.round(seconds * 1000),
        consent_music_usage: consentAccepted,
        consent_branded_policy: consentAccepted && commercial && brandedContent,
      });
      await loadJobs(selected.id);
      setNotice(
        "Direct Post job #" +
          job.id +
          " queued. PublishWorker will re-check Creator Info before sending.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to queue Direct Post");
    } finally {
      setBusy(false);
    }
  }

  async function queuePhoto() {
    if (!selected) return;
    const commonError = validateCommon();
    if (commonError) {
      setError(commonError);
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const job = await api.createPhotoPublish(selected.id, {
        photo_urls: parsedPhotoUrls,
        cover_index: photoCoverIndex,
        title: title.trim() || undefined,
        description: photoDescription.trim() || undefined,
        privacy_level: privacy,
        allow_comment: allowComment,
        auto_add_music: autoAddMusic,
        brand_content_toggle: commercial && brandedContent,
        brand_organic_toggle: commercial && yourBrand,
        is_aigc: isAigc,
        consent_music_usage: consentAccepted,
        consent_branded_policy: consentAccepted && commercial && brandedContent,
      });
      await loadJobs(selected.id);
      setNotice(
        "Photo Direct Post job #" +
          job.id +
          " queued. TikTok will pull the images from the verified URLs.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to queue photo Direct Post");
    } finally {
      setBusy(false);
    }
  }

  async function refreshJob(jobId: number) {
    setBusy(true);
    setError("");
    try {
      await api.refreshPublishJob(jobId);
      if (selectedId !== null) await loadJobs(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to refresh Direct Post status");
    } finally {
      setBusy(false);
    }
  }

  const declaration = commercial && brandedContent
    ? "By posting, you agree to TikTok's Branded Content Policy and Music Usage Confirmation."
    : "By posting, you agree to TikTok's Music Usage Confirmation.";

  return (
    <section className="panel direct-post-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">CONTENT POSTING API · VIDEO.PUBLISH</span>
          <h3>Direct Post Studio</h3>
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
          <span>Connect a TikTok account before using Direct Post.</span>
        </div>
      ) : !hasPublishScope ? (
        <div className="setup-box">
          <strong>video.publish permission required</strong>
          <p>
            Enable Direct Post in Content Posting API, request <code>video.publish</code>,
            then reconnect this account and authorize the new permission.
          </p>
        </div>
      ) : null}

      {hasPublishScope && (
        <>
          <div className="creator-card">
            <div className="creator-identity">
              {creator?.creator_avatar_url ? (
                <img src={creator.creator_avatar_url} alt="" />
              ) : (
                <div className="creator-placeholder">TT</div>
              )}
              <div>
                <strong>{creator?.creator_nickname || "Creator Info not loaded"}</strong>
                {creator?.creator_username && <span>@{creator.creator_username}</span>}
                <span>
                  Max video: {creator?.max_video_post_duration_sec ?? "—"} seconds
                </span>
              </div>
            </div>
            <button
              className="ghost"
              disabled={creatorBusy || selectedId === null}
              onClick={() => selectedId !== null && loadCreator(selectedId)}
            >
              {creatorBusy ? "Loading…" : "Refresh Creator Info"}
            </button>
          </div>

          <p className="direct-post-warning">
            TikTok requires the latest Creator Info for every Direct Post. Unaudited Direct
            Post clients are subject to TikTok's private-visibility restrictions until audit.
          </p>

          {error && <div className="error global-error">{error}</div>}
          {notice && <div className="notice">{notice}</div>}

          <div className="mode-tabs">
            <button
              className={mode === "VIDEO" ? "range-active" : "ghost"}
              onClick={() => {
                setMode("VIDEO");
                resetPostChoices();
              }}
            >
              Video
            </button>
            <button
              className={mode === "PHOTO" ? "range-active" : "ghost"}
              onClick={() => {
                setMode("PHOTO");
                resetPostChoices();
              }}
            >
              Photo
            </button>
          </div>

          <div className="direct-post-grid">
            <article className="direct-media-card">
              <span className="eyebrow">PREVIEW</span>
              {mode === "VIDEO" ? (
                <>
                  <form className="draft-form" onSubmit={uploadVideo}>
                    <label>
                      Store a video with duration metadata
                      <input
                        name="video"
                        type="file"
                        accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm"
                        disabled={busy}
                      />
                    </label>
                    <button type="submit" className="ghost" disabled={busy}>
                      Store video
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
                          {asset.original_name} · {formatDuration(asset.duration_seconds)}
                        </option>
                      ))}
                    </select>
                  </label>
                  {selectedMedia && (
                    <div className="direct-video-preview">
                      <video
                        controls
                        preload="metadata"
                        src={"/api/tiktok/media/" + selectedMedia.id + "/content"}
                      />
                      <span>
                        {selectedMedia.original_name} · {formatDuration(selectedMedia.duration_seconds)}
                      </span>
                    </div>
                  )}
                  <label>
                    Caption
                    <textarea
                      rows={4}
                      maxLength={2200}
                      value={title}
                      onChange={(event) => setTitle(event.target.value)}
                      placeholder="Caption, hashtags and mentions"
                    />
                  </label>
                  <label>
                    Cover frame · seconds
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      value={coverSeconds}
                      onChange={(event) => setCoverSeconds(event.target.value)}
                    />
                  </label>
                </>
              ) : (
                <>
                  <label>
                    Verified HTTPS photo URLs · one per line · max 35
                    <textarea
                      rows={6}
                      value={photoUrls}
                      onChange={(event) => setPhotoUrls(event.target.value)}
                      placeholder={"https://verified.example/photo-1.jpg\nhttps://verified.example/photo-2.webp"}
                    />
                  </label>
                  <div className="photo-preview-grid">
                    {parsedPhotoUrls.slice(0, 6).map((url, index) => (
                      <img src={url} alt={"Photo " + (index + 1)} key={url + index} />
                    ))}
                  </div>
                  <label>
                    Cover index
                    <input
                      type="number"
                      min="0"
                      max={Math.max(parsedPhotoUrls.length - 1, 0)}
                      value={photoCoverIndex}
                      onChange={(event) => setPhotoCoverIndex(Number(event.target.value))}
                    />
                  </label>
                  <label>
                    Title
                    <input
                      maxLength={90}
                      value={title}
                      onChange={(event) => setTitle(event.target.value)}
                    />
                  </label>
                  <label>
                    Description
                    <textarea
                      rows={4}
                      maxLength={4000}
                      value={photoDescription}
                      onChange={(event) => setPhotoDescription(event.target.value)}
                    />
                  </label>
                  <label className="check-label">
                    <input
                      type="checkbox"
                      checked={autoAddMusic}
                      onChange={(event) => setAutoAddMusic(event.target.checked)}
                    />
                    Auto add recommended music
                  </label>
                </>
              )}
            </article>

            <article className="direct-settings-card">
              <span className="eyebrow">POST SETTINGS</span>
              <label>
                Privacy · required
                <select
                  value={privacy}
                  onChange={(event) => setPrivacy(event.target.value)}
                >
                  <option value="" disabled>Select privacy</option>
                  {creator?.privacy_level_options.map((option) => (
                    <option
                      value={option}
                      key={option}
                      disabled={brandedContent && option === "SELF_ONLY"}
                    >
                      {privacyLabel(option)}
                    </option>
                  ))}
                </select>
              </label>

              <div className="interaction-box">
                <strong>Interactions</strong>
                <span>Nothing is enabled by default.</span>
                <label className="check-label">
                  <input
                    type="checkbox"
                    checked={allowComment}
                    disabled={Boolean(creator?.comment_disabled)}
                    onChange={(event) => setAllowComment(event.target.checked)}
                  />
                  Allow comments
                </label>
                {mode === "VIDEO" && (
                  <>
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={allowDuet}
                        disabled={Boolean(creator?.duet_disabled)}
                        onChange={(event) => setAllowDuet(event.target.checked)}
                      />
                      Allow Duet
                    </label>
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={allowStitch}
                        disabled={Boolean(creator?.stitch_disabled)}
                        onChange={(event) => setAllowStitch(event.target.checked)}
                      />
                      Allow Stitch
                    </label>
                  </>
                )}
              </div>

              <div className="interaction-box">
                <label className="check-label">
                  <input
                    type="checkbox"
                    checked={commercial}
                    onChange={(event) => setCommercial(event.target.checked)}
                  />
                  This content promotes a brand, product, service, or my business
                </label>
                {commercial && (
                  <div className="commercial-options">
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={yourBrand}
                        onChange={(event) => setYourBrand(event.target.checked)}
                      />
                      Your brand · Promotional content
                    </label>
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={brandedContent}
                        onChange={(event) => setBrandedContent(event.target.checked)}
                      />
                      Branded content · Paid partnership
                    </label>
                    {!yourBrand && !brandedContent && (
                      <span className="draft-failure">
                        Choose at least one commercial-content type.
                      </span>
                    )}
                  </div>
                )}
              </div>

              <label className="check-label">
                <input
                  type="checkbox"
                  checked={isAigc}
                  onChange={(event) => setIsAigc(event.target.checked)}
                />
                AI-generated content
              </label>

              <label className="consent-box">
                <input
                  type="checkbox"
                  checked={consentAccepted}
                  onChange={(event) => setConsentAccepted(event.target.checked)}
                />
                <span>{declaration}</span>
              </label>

              <button
                disabled={
                  busy ||
                  creatorBusy ||
                  !creator ||
                  !privacy ||
                  !consentAccepted ||
                  (commercial && !yourBrand && !brandedContent) ||
                  (mode === "VIDEO" && selectedAsset === null) ||
                  (mode === "PHOTO" && parsedPhotoUrls.length === 0)
                }
                onClick={mode === "VIDEO" ? queueVideo : queuePhoto}
              >
                {busy ? "Working…" : "Publish directly to TikTok"}
              </button>
            </article>
          </div>

          <div className="draft-jobs-head">
            <div>
              <strong>Direct Post jobs</strong>
              <span>PublishWorker checks status automatically.</span>
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
              <strong>No Direct Post jobs for this account.</strong>
              <span>Complete the review settings above to create one.</span>
            </div>
          ) : (
            <div className="draft-job-list">
              {jobs.map((job) => (
                <article className="draft-job" key={job.id}>
                  <div>
                    <strong>#{job.id} · {job.media_type} · {privacyLabel(job.privacy_level)}</strong>
                    <span>{new Date(job.created_at).toLocaleString()}</span>
                    {job.publish_id && <span>Publish ID: {job.publish_id}</span>}
                    {job.public_post_ids.length > 0 && (
                      <span>Post IDs: {job.public_post_ids.join(", ")}</span>
                    )}
                    {job.fail_reason && (
                      <span className="draft-failure">{job.fail_reason}</span>
                    )}
                  </div>
                  <div className="draft-job-actions">
                    <span className={"draft-status status-" + job.status.toLowerCase()}>
                      {job.status}
                    </span>
                    {job.publish_id && !["FAILED", "PUBLISH_COMPLETE"].includes(job.status) && (
                      <button
                        className="ghost"
                        disabled={busy}
                        onClick={() => refreshJob(job.id)}
                      >
                        Check status
                      </button>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}

function privacyLabel(value: string) {
  const labels: Record<string, string> = {
    PUBLIC_TO_EVERYONE: "Everyone",
    MUTUAL_FOLLOW_FRIENDS: "Friends",
    FOLLOWER_OF_CREATOR: "Followers",
    SELF_ONLY: "Only me",
  };
  return labels[value] || value;
}

function formatDuration(value?: number | null) {
  if (typeof value !== "number") return "duration unknown";
  if (value < 60) return value.toFixed(1) + "s";
  return Math.floor(value / 60) + "m " + Math.round(value % 60) + "s";
}
