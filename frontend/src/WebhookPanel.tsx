import { useEffect, useMemo, useState } from "react";

import { api, WebhookEvent } from "./api";
import { webhookStatusVi } from "./vi";

export default function WebhookPanel() {
  const [events, setEvents] = useState<WebhookEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const callbackUrl = useMemo(
    () => window.location.origin + "/api/tiktok/webhooks",
    [],
  );

  useEffect(() => {
    void loadEvents();
    const timer = window.setInterval(() => void loadEvents(), 15000);
    return () => window.clearInterval(timer);
  }, []);

  async function loadEvents() {
    setBusy(true);
    try {
      setEvents(await api.webhookEvents(100));
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải sự kiện gửi về từ TikTok");
    } finally {
      setBusy(false);
    }
  }

  async function copyCallback() {
    try {
      await navigator.clipboard.writeText(callbackUrl);
      setNotice("Đã sao chép URL nhận sự kiện từ TikTok.");
    } catch {
      setNotice("Sao chép thất bại. Hãy chọn URL callback và sao chép thủ công.");
    }
  }

  return (
    <section className="panel webhook-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">WEBHOOK</span>
          <h3>Sự kiện TikTok theo thời gian thực</h3>
        </div>
        <button className="ghost" disabled={busy} onClick={loadEvents}>
          {busy ? "Đang làm mới…" : "Làm mới sự kiện"}
        </button>
      </div>

      <div className="webhook-config-card">
        <div>
          <strong>URL callback</strong>
          <code>{callbackUrl}</code>
          <span>
            Thêm URL HTTPS này vào TikTok Developer Portal → Development configuration → Webhooks.
          </span>
        </div>
        <button className="ghost" onClick={copyCallback}>Sao chép URL</button>
      </div>

      <div className="webhook-security-grid">
        <div>
          <span>Xác minh chữ ký</span>
          <strong>HMAC-SHA256</strong>
        </div>
        <div>
          <span>Chống replay</span>
          <strong>Cửa sổ timestamp</strong>
        </div>
        <div>
          <span>Xử lý trùng lặp</span>
          <strong>Idempotent</strong>
        </div>
        <div>
          <span>Xử lý</span>
          <strong>Worker bất đồng bộ</strong>
        </div>
      </div>

      {notice && <div className="notice">{notice}</div>}
      {error && <div className="error global-error">{error}</div>}

      {events.length === 0 ? (
        <div className="empty-state">
          <strong>Chưa nhận được sự kiện gửi về nào từ TikTok.</strong>
          <span>
            Use TikTok Developer Portal's Test URL after configuring the callback.
          </span>
        </div>
      ) : (
        <div className="webhook-event-list">
          {events.map((event) => (
            <article className="webhook-event-row" key={event.id}>
              <div>
                <strong>{event.event_type}</strong>
                <span>{event.user_open_id || "Không có user_open_id"}</span>
                <span>
                  Received {new Date(event.received_at).toLocaleString("vi-VN")}
                </span>
                {event.error_detail && (
                  <span className="draft-failure">{event.error_detail}</span>
                )}
              </div>
              <div className="webhook-event-meta">
                <span className={"webhook-status status-" + event.status.toLowerCase()}>
                  {webhookStatusVi(event.status)}
                </span>
                <span>{event.attempts} attempt{event.attempts === 1 ? "" : "s"}</span>
                {event.processed_at && (
                  <span>{new Date(event.processed_at).toLocaleTimeString()}</span>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
