import { FormEvent, useEffect, useMemo, useState } from "react";

import { api, DraftJob, MediaAsset, TikTokAccount } from "./api";
import { readVideoDuration } from "./media";
import { jobStatusVi } from "./vi";

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
      setError(err instanceof Error ? err.message : "Không thể tải thư viện media");
    }
  }

  async function loadJobs(accountId: number) {
    try {
      setJobs(await api.draftJobs(accountId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải danh sách bản nháp");
    }
  }

  async function uploadVideo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const file = data.get("video");
    if (!(file instanceof File) || file.size === 0) {
      setError("Hãy chọn video MP4, MOV hoặc WebM trước.");
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
      setNotice("Video đã được lưu vào thư viện media và chưa được gửi sang TikTok.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tải video lên thất bại");
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
      setNotice("Tác vụ bản nháp #" + job.id + " đã vào hàng đợi. DraftWorker sẽ gửi sang TikTok.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể đưa video vào hàng đợi bản nháp");
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
      setNotice("Tác vụ ảnh nháp #" + job.id + " đã được đưa vào hàng đợi gửi tới Hộp thư TikTok.");
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể đưa ảnh vào hàng đợi bản nháp");
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
      setError(err instanceof Error ? err.message : "Không thể làm mới trạng thái bản nháp");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel draft-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">CONTENT POSTING API · VIDEO.UPLOAD</span>
          <h3>Trình tải bản nháp</h3>
        </div>
        {accounts.length > 1 && (
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
                {account.display_name || account.username || "Tài khoản #" + account.id}
              </option>
            ))}
          </select>
        )}
      </div>

      {!selected ? (
        <div className="empty-state">
          <strong>Chưa có tài khoản được kết nối.</strong>
          <span>Hãy kết nối một tài khoản TikTok trước khi tạo bản nháp.</span>
        </div>
      ) : !hasUploadScope ? (
        <div className="setup-box">
          <strong>Cần quyền video.upload</strong>
          <p>
            Bật Content Posting API và quyền <code>video.upload</code> trong TikTok Developer Portal, sau đó kết nối lại tài khoản để cấp quyền mới. Media vẫn có thể được lưu cục bộ trước khi quyền được cấp.
          </p>
        </div>
      ) : null}

      {error && <div className="error global-error">{error}</div>}
      {notice && <div className="notice">{notice}</div>}

      <div className="draft-studio-grid">
        <article className="draft-card">
          <span className="eyebrow">BẢN NHÁP VIDEO</span>
          <h4>Thư viện media cục bộ</h4>
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
              {busy ? "Đang xử lý…" : "Lưu video"}
            </button>
          </form>

          <label>
            Video đã lưu
            <select
              value={selectedAsset ?? ""}
              onChange={(event) => setSelectedAsset(Number(event.target.value))}
              disabled={assets.length === 0}
            >
              {assets.length === 0 && <option value="">Chưa có video được lưu</option>}
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
            Gửi video vào hàng đợi bản nháp TikTok
          </button>
          <p className="draft-help">
            TikTok sẽ gửi video đã tải lên tới Hộp thư của nhà sáng tạo. Người dùng mở TikTok để chỉnh sửa và hoàn tất bài đăng.
          </p>
        </article>

        <article className="draft-card">
          <span className="eyebrow">BẢN NHÁP ẢNH</span>
          <h4>URL ảnh HTTPS đã xác minh</h4>
          <form className="draft-form" onSubmit={queuePhotos}>
            <label>
              URL ảnh · mỗi dòng một URL · tối đa 35
              <textarea
                name="photo_urls"
                rows={5}
                placeholder={"https://verified.example/photo-1.jpg\nhttps://verified.example/photo-2.webp"}
                disabled={busy}
              />
            </label>
            <div className="draft-inline">
              <label>
                Vị trí ảnh bìa
                <input name="cover_index" type="number" min="0" defaultValue="0" />
              </label>
              <label className="check-label">
                <input name="is_aigc" type="checkbox" />
                Nội dung do AI tạo
              </label>
            </div>
            <label>
              Tiêu đề
              <input name="title" maxLength={90} />
            </label>
            <label>
              Mô tả
              <textarea name="description" rows={3} maxLength={4000} />
            </label>
            <button type="submit" disabled={busy || !hasUploadScope}>
              Gửi ảnh vào hàng đợi bản nháp
            </button>
          </form>
        </article>
      </div>

      <div className="draft-jobs-head">
        <div>
          <strong>Tác vụ bản nháp</strong>
          <span>Tự động làm mới mỗi 15 giây</span>
        </div>
        <button
          className="ghost"
          disabled={busy || selectedId === null}
          onClick={() => selectedId !== null && loadJobs(selectedId)}
        >
          Làm mới danh sách
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="empty-state">
          <strong>Tài khoản này chưa có tác vụ bản nháp.</strong>
          <span>Hãy đưa video hoặc ảnh vào hàng đợi để bắt đầu.</span>
        </div>
      ) : (
        <div className="draft-job-list">
          {jobs.map((job) => (
            <article className="draft-job" key={job.id}>
              <div>
                <strong>#{job.id} · {job.media_type}</strong>
                <span>{new Date(job.created_at).toLocaleString("vi-VN")}</span>
                {job.publish_id && <span>Publish ID: {job.publish_id}</span>}
                {job.fail_reason && <span className="draft-failure">{job.fail_reason}</span>}
                {job.status === "SEND_TO_USER_INBOX" && (
                  <span className="draft-inbox">
                    Đã gửi thông báo tới Hộp thư TikTok — mở TikTok để hoàn tất chỉnh sửa/đăng bài.
                  </span>
                )}
              </div>
              <div className="draft-job-actions">
                <span className={"draft-status status-" + job.status.toLowerCase()}>
                  {jobStatusVi(job.status)}
                </span>
                {job.publish_id && !["FAILED", "PUBLISH_COMPLETE"].includes(job.status) && (
                  <button className="ghost" disabled={busy} onClick={() => refreshJob(job.id)}>
                    Kiểm tra trạng thái
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
