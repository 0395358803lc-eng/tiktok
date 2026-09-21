import { useEffect, useMemo, useState } from "react";

import { api, TikTokAccount, TikTokVideo } from "./api";

export type VideoView = "list" | "detail" | "stats" | "embed";

type Props = {
  account: TikTokAccount;
  view: VideoView;
};

export default function AccountVideoWorkspace({ account, view }: Props) {
  const [videos, setVideos] = useState<TikTokVideo[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<number | null>(null);
  const [cursor, setCursor] = useState<number | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const hasScope = account.scopes.includes("video.list");
  const selectedVideo = useMemo(
    () => videos.find((video) => video.id === selectedVideoId) ?? videos[0] ?? null,
    [videos, selectedVideoId],
  );

  useEffect(() => {
    setCursor(null);
    setHasMore(false);
    setSelectedVideoId(null);
    void loadLocal();
  }, [account.id]);

  async function loadLocal() {
    try {
      const rows = await api.tiktokVideos(account.id);
      setVideos(rows);
      setSelectedVideoId((current) =>
        current && rows.some((video) => video.id === current)
          ? current
          : rows[0]?.id ?? null,
      );
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải thư viện video");
    }
  }

  async function sync(nextCursor: number | null) {
    setBusy(true);
    setError("");
    try {
      const result = await api.syncTikTokVideos(account.id, nextCursor, 20);
      setCursor(result.cursor ?? null);
      setHasMore(result.has_more);
      await loadLocal();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đồng bộ video thất bại");
    } finally {
      setBusy(false);
    }
  }

  async function refreshMetadata() {
    if (!selectedVideo) return;
    setBusy(true);
    setError("");
    try {
      await api.refreshTikTokVideos(account.id, [selectedVideo.video_id]);
      await loadLocal();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Làm mới dữ liệu video thất bại");
    } finally {
      setBusy(false);
    }
  }

  if (!hasScope) {
    return (
      <PermissionRequired
        scope="video.list"
        text="Tài khoản chưa cấp quyền đọc danh sách video công khai."
      />
    );
  }

  return (
    <section className="account-feature-card">
      <div className="feature-card-head">
        <div>
          <span className="eyebrow">DISPLAY API · VIDEO.LIST</span>
          <h3>{viewTitle(view)}</h3>
        </div>
        <div className="feature-actions">
          <button disabled={busy} onClick={() => sync(null)}>
            {busy ? "Đang xử lý…" : "Đồng bộ video mới"}
          </button>
          <button
            className="ghost"
            disabled={busy || !hasMore || cursor === null}
            onClick={() => sync(cursor)}
          >
            Đồng bộ video cũ
          </button>
        </div>
      </div>

      {error && <div className="error global-error">{error}</div>}

      {videos.length === 0 ? (
        <div className="empty-state">
          <strong>Chưa có video được đồng bộ.</strong>
          <span>Bấm “Đồng bộ video mới” để lấy video công khai từ tài khoản này.</span>
        </div>
      ) : (
        <>
          {view !== "list" && (
            <div className="video-selector-row">
              <label>
                Chọn video
                <select
                  value={selectedVideo?.id ?? ""}
                  onChange={(event) => setSelectedVideoId(Number(event.target.value))}
                >
                  {videos.map((video) => (
                    <option value={video.id} key={video.id}>
                      {video.title || video.video_description || "Video " + video.video_id}
                    </option>
                  ))}
                </select>
              </label>
              <button className="ghost" disabled={busy} onClick={refreshMetadata}>
                Làm mới video đang chọn
              </button>
            </div>
          )}

          {view === "list" && <VideoList videos={videos} onSelect={setSelectedVideoId} />}
          {view === "detail" && selectedVideo && <VideoDetail video={selectedVideo} />}
          {view === "stats" && selectedVideo && <VideoStats video={selectedVideo} />}
          {view === "embed" && selectedVideo && <VideoEmbed video={selectedVideo} />}
        </>
      )}
    </section>
  );
}

function VideoList({
  videos,
  onSelect,
}: {
  videos: TikTokVideo[];
  onSelect: (id: number) => void;
}) {
  return (
    <div className="video-grid">
      {videos.map((video) => (
        <article className="video-card" key={video.id}>
          <div className="video-cover">
            {video.cover_image_url ? (
              <img src={video.cover_image_url} alt="" loading="lazy" />
            ) : (
              <div className="video-cover-placeholder">VIDEO</div>
            )}
            {typeof video.duration === "number" && (
              <span className="video-duration">{video.duration}s</span>
            )}
          </div>
          <div className="video-body">
            <strong>{video.title || video.video_description || "Video TikTok"}</strong>
            <span>
              {video.create_time
                ? new Date(video.create_time).toLocaleString("vi-VN")
                : "Không có ngày đăng"}
            </span>
            <div className="video-metrics">
              <Metric label="Lượt xem" value={video.view_count} />
              <Metric label="Lượt thích" value={video.like_count} />
              <Metric label="Bình luận" value={video.comment_count} />
              <Metric label="Chia sẻ" value={video.share_count} />
            </div>
            <button className="ghost" onClick={() => onSelect(video.id)}>
              Chọn video này
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}

function VideoDetail({ video }: { video: TikTokVideo }) {
  return (
    <div className="video-detail-layout">
      <div className="video-detail-cover">
        {video.cover_image_url ? (
          <img src={video.cover_image_url} alt="" />
        ) : (
          <div className="video-cover-placeholder">VIDEO</div>
        )}
      </div>
      <div className="video-detail-fields">
        <Field label="Video ID" value={video.video_id} />
        <Field label="Caption / tiêu đề" value={video.title || video.video_description} />
        <Field
          label="Ngày đăng"
          value={video.create_time ? new Date(video.create_time).toLocaleString("vi-VN") : null}
        />
        <Field label="Thời lượng" value={numberWithUnit(video.duration, " giây")} />
        <Field
          label="Kích thước"
          value={
            typeof video.width === "number" && typeof video.height === "number"
              ? video.width + " × " + video.height
              : null
          }
        />
        <Field label="URL chia sẻ" value={video.share_url} link />
        <Field label="Embed link" value={video.embed_link} link />
        <Field label="Nhãn AI" value={video.is_aigc ? "Có" : "Không / chưa có dữ liệu"} />
        <Field label="Đồng bộ gần nhất" value={new Date(video.synced_at).toLocaleString("vi-VN")} />
      </div>
    </div>
  );
}

function VideoStats({ video }: { video: TikTokVideo }) {
  return (
    <div className="video-stat-grid">
      <MetricCard label="Lượt xem" value={video.view_count} />
      <MetricCard label="Lượt thích" value={video.like_count} />
      <MetricCard label="Bình luận" value={video.comment_count} />
      <MetricCard label="Chia sẻ" value={video.share_count} />
    </div>
  );
}

function VideoEmbed({ video }: { video: TikTokVideo }) {
  return (
    <div className="embed-view">
      {video.embed_link ? (
        <>
          <div className="embed-preview-box">
            <iframe
              title={video.title || "Video TikTok"}
              src={video.embed_link}
              loading="lazy"
              allowFullScreen
            />
          </div>
          <div className="embed-actions">
            <code>{video.embed_link}</code>
            <a href={video.embed_link} target="_blank" rel="noreferrer">
              Mở liên kết nhúng
            </a>
          </div>
        </>
      ) : (
        <div className="empty-state">
          <strong>Video này chưa có embed link.</strong>
          <span>Làm mới metadata hoặc chọn video khác.</span>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value?: number | null }) {
  return (
    <span className="video-metric">
      <small>{label}</small>
      <strong>{typeof value === "number" ? value.toLocaleString("vi-VN") : "—"}</strong>
    </span>
  );
}

function MetricCard({ label, value }: { label: string; value?: number | null }) {
  return (
    <article className="account-stat-card">
      <span>{label}</span>
      <strong>{typeof value === "number" ? value.toLocaleString("vi-VN") : "—"}</strong>
    </article>
  );
}

function Field({
  label,
  value,
  link = false,
}: {
  label: string;
  value?: string | null;
  link?: boolean;
}) {
  return (
    <div className="profile-field">
      <span>{label}</span>
      {link && value ? (
        <a href={value} target="_blank" rel="noreferrer">{value}</a>
      ) : (
        <strong>{value || "—"}</strong>
      )}
    </div>
  );
}

function PermissionRequired({ scope, text }: { scope: string; text: string }) {
  return (
    <div className="permission-required">
      <div>
        <strong>Chưa cấp quyền {scope}</strong>
        <p>{text}</p>
      </div>
      <code>{scope}</code>
    </div>
  );
}

function numberWithUnit(value?: number | null, unit = "") {
  return typeof value === "number" ? value.toLocaleString("vi-VN") + unit : null;
}

function viewTitle(view: VideoView) {
  const map: Record<VideoView, string> = {
    list: "Danh sách video",
    detail: "Chi tiết video",
    stats: "Thống kê từng video",
    embed: "Nhúng video",
  };
  return map[view];
}
