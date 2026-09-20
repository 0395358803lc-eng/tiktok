import { useEffect, useMemo, useState } from "react";

import { api, TikTokAccount, TikTokVideo } from "./api";

type Props = {
  accounts: TikTokAccount[];
};

export default function VideoLibrary({ accounts }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(accounts[0]?.id ?? null);
  const [videos, setVideos] = useState<TikTokVideo[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const selected = useMemo(
    () => accounts.find((account) => account.id === selectedId) ?? null,
    [accounts, selectedId],
  );

  useEffect(() => {
    if (selectedId === null && accounts.length > 0) {
      setSelectedId(accounts[0].id);
    } else if (selectedId !== null && !accounts.some((account) => account.id === selectedId)) {
      setSelectedId(accounts[0]?.id ?? null);
    }
  }, [accounts, selectedId]);

  useEffect(() => {
    if (selectedId !== null) void loadLocal(selectedId);
    else setVideos([]);
  }, [selectedId]);

  async function loadLocal(accountId: number) {
    try {
      const rows = await api.tiktokVideos(accountId);
      setVideos(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load video library");
    }
  }

  async function syncPage(nextCursor: number | null) {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.syncTikTokVideos(selected.id, nextCursor, 20);
      setCursor(result.cursor ?? null);
      setHasMore(result.has_more);
      await loadLocal(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Video synchronization failed");
    } finally {
      setBusy(false);
    }
  }

  async function refreshVisible() {
    if (!selected || videos.length === 0) return;
    setBusy(true);
    setError("");
    try {
      const ids = videos.slice(0, 20).map((video) => video.video_id);
      await api.refreshTikTokVideos(selected.id, ids);
      await loadLocal(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Video metadata refresh failed");
    } finally {
      setBusy(false);
    }
  }

  const hasVideoScope = Boolean(selected?.scopes.includes("video.list"));

  return (
    <section className="panel video-library">
      <div className="section-head">
        <div>
          <span className="eyebrow">DISPLAY API</span>
          <h3>Video Library</h3>
        </div>
        {accounts.length > 0 && (
          <select
            className="video-account-select"
            value={selectedId ?? ""}
            onChange={(event) => {
              setSelectedId(Number(event.target.value));
              setCursor(null);
              setHasMore(false);
              setError("");
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

      {accounts.length === 0 ? (
        <div className="empty-state">
          <strong>No TikTok account is connected.</strong>
          <span>Connect an account before using the video library.</span>
        </div>
      ) : !hasVideoScope ? (
        <div className="setup-box">
          <strong>video.list permission required</strong>
          <p>
            Enable <code>video.list</code> in the TikTok Developer Portal, add it to the
            configured scopes, then reconnect this account and authorize the new permission.
          </p>
        </div>
      ) : (
        <>
          <div className="video-actions">
            <button disabled={busy} onClick={() => syncPage(null)}>
              {busy ? "Working…" : "Sync latest"}
            </button>
            <button
              className="ghost"
              disabled={busy || !hasMore || cursor === null}
              onClick={() => syncPage(cursor)}
            >
              Sync older
            </button>
            <button
              className="ghost"
              disabled={busy || videos.length === 0}
              onClick={refreshVisible}
            >
              Refresh metadata
            </button>
            <span>{videos.length} stored videos</span>
          </div>

          {error && <div className="error global-error">{error}</div>}

          {videos.length === 0 ? (
            <div className="empty-state">
              <strong>No videos synchronized yet.</strong>
              <span>Use Sync latest to import public videos from the authorized account.</span>
            </div>
          ) : (
            <div className="video-grid">
              {videos.map((video) => (
                <article className="video-card" key={video.id}>
                  <div className="video-cover">
                    {video.cover_image_url ? (
                      <img src={video.cover_image_url} alt="" loading="lazy" />
                    ) : (
                      <div className="video-cover-placeholder">VIDEO</div>
                    )}
                    {video.duration !== null && video.duration !== undefined && (
                      <span className="video-duration">{video.duration}s</span>
                    )}
                  </div>
                  <div className="video-body">
                    <strong>{video.title || video.video_description || "TikTok video"}</strong>
                    {video.create_time && (
                      <span>{new Date(video.create_time).toLocaleString()}</span>
                    )}
                    <div className="video-metrics">
                      <Metric label="Views" value={video.view_count} />
                      <Metric label="Likes" value={video.like_count} />
                      <Metric label="Comments" value={video.comment_count} />
                      <Metric label="Shares" value={video.share_count} />
                    </div>
                    <div className="video-links">
                      {video.share_url && (
                        <a href={video.share_url} target="_blank" rel="noreferrer">
                          Open on TikTok
                        </a>
                      )}
                      {video.embed_link && (
                        <a href={video.embed_link} target="_blank" rel="noreferrer">
                          Embed
                        </a>
                      )}
                      {video.is_aigc && <span>AI-generated tag</span>}
                    </div>
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

function Metric({ label, value }: { label: string; value?: number | null }) {
  return (
    <span className="video-metric">
      <small>{label}</small>
      <strong>{typeof value === "number" ? value.toLocaleString() : "—"}</strong>
    </span>
  );
}
