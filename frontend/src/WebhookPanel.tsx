import { useEffect, useMemo, useState } from "react";

import { api, WebhookEvent } from "./api";

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
      setError(err instanceof Error ? err.message : "Unable to load webhook events");
    } finally {
      setBusy(false);
    }
  }

  async function copyCallback() {
    try {
      await navigator.clipboard.writeText(callbackUrl);
      setNotice("Webhook callback copied.");
    } catch {
      setNotice("Copy failed. Select the callback URL manually.");
    }
  }

  return (
    <section className="panel webhook-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">WEBHOOKS</span>
          <h3>Realtime TikTok events</h3>
        </div>
        <button className="ghost" disabled={busy} onClick={loadEvents}>
          {busy ? "Refreshing…" : "Refresh events"}
        </button>
      </div>

      <div className="webhook-config-card">
        <div>
          <strong>Callback URL</strong>
          <code>{callbackUrl}</code>
          <span>
            Add this HTTPS URL in TikTok Developer Portal → Development configuration → Webhooks.
          </span>
        </div>
        <button className="ghost" onClick={copyCallback}>Copy URL</button>
      </div>

      <div className="webhook-security-grid">
        <div>
          <span>Signature verification</span>
          <strong>HMAC-SHA256</strong>
        </div>
        <div>
          <span>Replay protection</span>
          <strong>Timestamp window</strong>
        </div>
        <div>
          <span>Duplicate handling</span>
          <strong>Idempotent</strong>
        </div>
        <div>
          <span>Processing</span>
          <strong>Async worker</strong>
        </div>
      </div>

      {notice && <div className="notice">{notice}</div>}
      {error && <div className="error global-error">{error}</div>}

      {events.length === 0 ? (
        <div className="empty-state">
          <strong>No TikTok webhook has been received yet.</strong>
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
                <span>{event.user_open_id || "No user open_id"}</span>
                <span>
                  Received {new Date(event.received_at).toLocaleString()}
                </span>
                {event.error_detail && (
                  <span className="draft-failure">{event.error_detail}</span>
                )}
              </div>
              <div className="webhook-event-meta">
                <span className={"webhook-status status-" + event.status.toLowerCase()}>
                  {event.status}
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
