import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  api,
  CreatorInfo,
  MediaAsset,
  PublishJob,
  TikTokAccount,
} from "./api";
import { readVideoDuration } from "./media";
import { jobStatusVi } from "./vi";

type Props = {
  accounts: TikTokAccount[];
  initialMode?: Mode;
};

type Mode = "VIDEO" | "PHOTO";

export default function DirectPostPanel({ accounts, initialMode = "VIDEO" }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(accounts[0]?.id ?? null);
  const [mode, setMode] = useState<Mode>(initialMode);
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
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [scheduledAt, setScheduledAt] = useState("");
  const [maxRetries, setMaxRetries] = useState(2);
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
    setMode(initialMode);
    resetPostChoices();
  }, [initialMode]);

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
    setScheduleEnabled(false);
    setScheduledAt("");
    setMaxRetries(2);
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
      setError(err instanceof Error ? err.message : "Không thể tải thông tin nhà sáng tạo");
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
      setError(err instanceof Error ? err.message : "Không thể tải thư viện media");
    }
  }

  async function loadJobs(accountId: number) {
    try {
      setJobs(await api.publishJobs(accountId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải danh sách tác vụ đăng trực tiếp");
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
      if (
        creator?.max_video_post_duration_sec &&
        duration > creator.max_video_post_duration_sec
      ) {
        throw new Error(
          "Video dài hơn giới hạn hiện tại của tài khoản là " +
            creator.max_video_post_duration_sec +
            " giây.",
        );
      }
      const asset = await api.uploadVideoMedia(file, duration);
      await loadAssets();
      setSelectedAsset(asset.id);
      form.reset();
      setNotice(
        "Video đã được lưu kèm dữ liệu thời lượng. Hãy kiểm tra phần xem trước và thiết lập trước khi đăng.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tải video lên thất bại");
    } finally {
      setBusy(false);
    }
  }

  function validateCommon(): string | null {
    if (!creator) return "Hãy tải thông tin nhà sáng tạo trước khi đăng.";
    if (!privacy) return "Hãy chọn quyền xem bài đăng.";
    if (!consentAccepted) return "Hãy xác nhận điều khoản đăng bài bắt buộc của TikTok.";
    if (commercial && !yourBrand && !brandedContent) {
      return "Hãy chọn Thương hiệu của tôi, Nội dung hợp tác trả phí hoặc cả hai.";
    }
    if (brandedContent && privacy === "SELF_ONLY") {
      return "Nội dung hợp tác trả phí không thể dùng quyền xem Chỉ mình tôi.";
    }
    return null;
  }

  function resolveScheduledAt(): string | undefined {
    if (!scheduleEnabled) return undefined;
    if (!scheduledAt) throw new Error("Hãy chọn ngày giờ đăng.");
    const value = new Date(scheduledAt);
    if (!Number.isFinite(value.getTime())) throw new Error("Thời gian đặt lịch không hợp lệ.");
    if (value.getTime() <= Date.now() + 30_000) {
      throw new Error("Thời gian đặt lịch phải cách hiện tại ít nhất 30 giây.");
    }
    return value.toISOString();
  }

  async function queueVideo() {
    if (!selected || selectedAsset === null) return;
    const commonError = validateCommon();
    if (commonError) {
      setError(commonError);
      return;
    }
    if (!selectedMedia?.duration_seconds) {
      setError("Video đã lưu không có dữ liệu thời lượng. Hãy tải lại video trước khi đăng trực tiếp.");
      return;
    }
    if (
      creator?.max_video_post_duration_sec &&
      selectedMedia.duration_seconds > creator.max_video_post_duration_sec
    ) {
      setError("Video đã chọn vượt quá thời lượng tối đa hiện tại của tài khoản.");
      return;
    }

    const seconds = coverSeconds.trim() ? Number(coverSeconds) : undefined;
    if (seconds !== undefined && (!Number.isFinite(seconds) || seconds < 0)) {
      setError("Thời điểm ảnh bìa phải là số giây không âm.");
      return;
    }

    let scheduledIso: string | undefined;
    try {
      scheduledIso = resolveScheduledAt();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Thời gian đặt lịch không hợp lệ");
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
        scheduled_at: scheduledIso,
        max_retries: maxRetries,
      });
      await loadJobs(selected.id);
      setNotice(
        "Tác vụ đăng trực tiếp #" +
          job.id +
          (scheduleEnabled
          ? " đã được lên lịch. Hệ thống sẽ đưa bài vào hàng đợi khi đến giờ."
          : " đã vào hàng đợi. Hệ thống sẽ kiểm tra lại thông tin nhà sáng tạo trước khi gửi."),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể đưa bài đăng trực tiếp vào hàng đợi");
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
    let scheduledIso: string | undefined;
    try {
      scheduledIso = resolveScheduledAt();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Thời gian đặt lịch không hợp lệ");
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
        scheduled_at: scheduledIso,
        max_retries: maxRetries,
      });
      await loadJobs(selected.id);
      setNotice(
        "Tác vụ đăng ảnh trực tiếp #" +
          job.id +
          (scheduleEnabled
          ? " đã được lên lịch. Hệ thống sẽ đưa bài vào hàng đợi khi đến giờ."
          : " đã vào hàng đợi. TikTok sẽ lấy ảnh từ các URL đã được xác minh."),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể đưa bài đăng ảnh vào hàng đợi");
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
      setError(err instanceof Error ? err.message : "Không thể làm mới trạng thái đăng trực tiếp");
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
          <h3>Trình đăng bài trực tiếp</h3>
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
          <span>Hãy kết nối tài khoản TikTok trước khi dùng tính năng đăng trực tiếp.</span>
        </div>
      ) : !hasPublishScope ? (
        <div className="setup-box">
          <strong>Cần quyền video.publish</strong>
          <p>
            Bật tính năng đăng trực tiếp (Direct Post) trong Content Posting API, xin quyền <code>video.publish</code>, sau đó kết nối lại tài khoản để cấp quyền mới.
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
                <strong>{creator?.creator_nickname || "Chưa tải thông tin nhà sáng tạo"}</strong>
                {creator?.creator_username && <span>@{creator.creator_username}</span>}
                <span>
                  Video tối đa: {creator?.max_video_post_duration_sec ?? "—"} giây
                </span>
              </div>
            </div>
            <button
              className="ghost"
              disabled={creatorBusy || selectedId === null}
              onClick={() => selectedId !== null && loadCreator(selectedId)}
            >
              {creatorBusy ? "Đang tải…" : "Làm mới thông tin nhà sáng tạo"}
            </button>
          </div>

          <p className="direct-post-warning">
            TikTok yêu cầu Creator Info mới nhất cho mỗi lần đăng trực tiếp. Khi ứng dụng chưa được audit,
            Direct Post chỉ được dùng với quyền xem SELF_ONLY và tài khoản TikTok đích phải đang ở chế độ
            Riêng tư (Private). Nếu tài khoản đang công khai, TikTok sẽ chặn yêu cầu trước khi tạo publish_id.
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
              <span className="eyebrow">XEM TRƯỚC</span>
              {mode === "VIDEO" ? (
                <>
                  <form className="draft-form" onSubmit={uploadVideo}>
                    <label>
                      Lưu video kèm dữ liệu thời lượng
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
                    Video đã lưu
                    <select
                      value={selectedAsset ?? ""}
                      onChange={(event) => setSelectedAsset(Number(event.target.value))}
                      disabled={assets.length === 0}
                    >
                      {assets.length === 0 && <option value="">Chưa có video được lưu</option>}
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
                    Chú thích
                    <textarea
                      rows={4}
                      maxLength={2200}
                      value={title}
                      onChange={(event) => setTitle(event.target.value)}
                      placeholder="Chú thích, hashtag và mention"
                    />
                  </label>
                  <label>
                    Khung ảnh bìa · giây
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
                    URL ảnh HTTPS đã xác minh · mỗi dòng một URL · tối đa 35
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
                    Tự động thêm nhạc được đề xuất
                  </label>
                </>
              )}
            </article>

            <article className="direct-settings-card">
              <span className="eyebrow">THIẾT LẬP BÀI ĐĂNG</span>
              <label>
                Quyền xem · bắt buộc
                <select
                  value={privacy}
                  onChange={(event) => setPrivacy(event.target.value)}
                >
                  <option value="" disabled>Chọn quyền xem</option>
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
                <strong>Tương tác</strong>
                <span>Mặc định không bật tùy chọn nào.</span>
                <label className="check-label">
                  <input
                    type="checkbox"
                    checked={allowComment}
                    disabled={Boolean(creator?.comment_disabled)}
                    onChange={(event) => setAllowComment(event.target.checked)}
                  />
                  Cho phép bình luận
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
                      Cho phép Duet
                    </label>
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={allowStitch}
                        disabled={Boolean(creator?.stitch_disabled)}
                        onChange={(event) => setAllowStitch(event.target.checked)}
                      />
                      Cho phép Stitch
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
                  Nội dung này quảng bá thương hiệu, sản phẩm, dịch vụ hoặc doanh nghiệp của tôi
                </label>
                {commercial && (
                  <div className="commercial-options">
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={yourBrand}
                        onChange={(event) => setYourBrand(event.target.checked)}
                      />
                      Thương hiệu của tôi · Nội dung quảng bá
                    </label>
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={brandedContent}
                        onChange={(event) => setBrandedContent(event.target.checked)}
                      />
                      Nội dung có thương hiệu · Hợp tác trả phí
                    </label>
                    {!yourBrand && !brandedContent && (
                      <span className="draft-failure">
                        Hãy chọn ít nhất một loại nội dung thương mại.
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
                Nội dung do AI tạo
              </label>

              <label className="consent-box">
                <input
                  type="checkbox"
                  checked={consentAccepted}
                  onChange={(event) => setConsentAccepted(event.target.checked)}
                />
                <span>{declaration}</span>
              </label>

              <div className="direct-schedule-box">
                <label className="check-label">
                  <input
                    type="checkbox"
                    checked={scheduleEnabled}
                    onChange={(event) => setScheduleEnabled(event.target.checked)}
                  />
                  Lên lịch thay vì đăng ngay
                </label>
                {scheduleEnabled && (
                  <div className="schedule-input-grid">
                    <label>
                      Ngày giờ địa phương
                      <input
                        type="datetime-local"
                        value={scheduledAt}
                        onChange={(event) => setScheduledAt(event.target.value)}
                      />
                    </label>
                    <label>
                      Số lần thử lại an toàn tối đa
                      <input
                        type="number"
                        min="0"
                        max="5"
                        value={maxRetries}
                        onChange={(event) => setMaxRetries(Number(event.target.value))}
                      />
                    </label>
                    <span>Trình duyệt sẽ chuyển thời gian sang UTC trước khi gửi tới bộ lập lịch.</span>
                  </div>
                )}
              </div>

              <button
                disabled={
                  busy ||
                  creatorBusy ||
                  !creator ||
                  !privacy ||
                  !consentAccepted ||
                  (commercial && !yourBrand && !brandedContent) ||
                  (mode === "VIDEO" && selectedAsset === null) ||
                  (mode === "PHOTO" && parsedPhotoUrls.length === 0) ||
                  (scheduleEnabled && !scheduledAt)
                }
                onClick={mode === "VIDEO" ? queueVideo : queuePhoto}
              >
                {busy ? "Đang xử lý…" : scheduleEnabled ? "Lên lịch đăng trực tiếp" : "Đăng trực tiếp lên TikTok"}
              </button>
            </article>
          </div>

          <div className="draft-jobs-head">
            <div>
              <strong>Tác vụ đăng trực tiếp</strong>
              <span>Tiến trình đăng bài tự động kiểm tra trạng thái.</span>
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
              <strong>Tài khoản này chưa có tác vụ đăng trực tiếp.</strong>
              <span>Hoàn tất các thiết lập phía trên để tạo tác vụ.</span>
            </div>
          ) : (
            <div className="draft-job-list">
              {jobs.map((job) => (
                <article className="draft-job" key={job.id}>
                  <div>
                    <strong>#{job.id} · {job.media_type} · {privacyLabel(job.privacy_level)}</strong>
                    <span>{new Date(job.created_at).toLocaleString("vi-VN")}</span>
                    <span>Hàng đợi: {jobStatusVi(job.schedule_status)}</span>
                    {job.scheduled_at && (
                      <span>Đã lên lịch: {new Date(job.scheduled_at).toLocaleString("vi-VN")}</span>
                    )}
                    {job.publish_id && <span>Publish ID: {job.publish_id}</span>}
                    {job.public_post_ids.length > 0 && (
                      <span>Post ID: {job.public_post_ids.join(", ")}</span>
                    )}
                    {job.fail_reason && (
                      <span className="draft-failure">{job.fail_reason}</span>
                    )}
                  </div>
                  <div className="draft-job-actions">
                    <span className={"draft-status status-" + job.status.toLowerCase()}>
                      {jobStatusVi(job.status)}
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
    PUBLIC_TO_EVERYONE: "Mọi người",
    MUTUAL_FOLLOW_FRIENDS: "Bạn bè",
    FOLLOWER_OF_CREATOR: "Người theo dõi",
    SELF_ONLY: "Chỉ mình tôi",
  };
  return labels[value] || value;
}

function formatDuration(value?: number | null) {
  if (typeof value !== "number") return "không xác định thời lượng";
  if (value < 60) return value.toFixed(1) + "s";
  return Math.floor(value / 60) + "m " + Math.round(value % 60) + "s";
}
