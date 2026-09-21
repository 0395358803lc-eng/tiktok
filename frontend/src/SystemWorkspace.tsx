import OperationsPanel from "./OperationsPanel";
import ReviewPackagePanel from "./ReviewPackagePanel";
import WebhookPanel from "./WebhookPanel";
import { AuditEvent, TikTokAccount } from "./api";
import { auditStatusVi } from "./vi";

type Props = {
  mode: "system" | "events";
  accounts: TikTokAccount[];
  auditEvents: AuditEvent[];
  onReload: () => Promise<void>;
  busy: boolean;
};

export default function SystemWorkspace({ mode, accounts, auditEvents, onReload, busy }: Props) {
  if (mode === "events") {
    return (
      <div className="system-workspace">
        <div className="workspace-page-title">
          <span className="eyebrow">SỰ KIỆN & NHẬT KÝ</span>
          <h2>Sự kiện hệ thống</h2>
          <p>Theo dõi Webhook TikTok và lịch sử thao tác của toàn bộ tài khoản.</p>
        </div>
        <WebhookPanel />
        <AuditPanel events={auditEvents} onReload={onReload} busy={busy} />
      </div>
    );
  }

  return (
    <div className="system-workspace">
      <div className="workspace-page-title">
        <span className="eyebrow">QUẢN TRỊ HỆ THỐNG</span>
        <h2>Hệ thống & vận hành</h2>
        <p>Quản lý sức khỏe account, scope, worker, backup, production gate và hồ sơ review.</p>
      </div>
      <OperationsPanel accounts={accounts} onChanged={onReload} />
      <ReviewPackagePanel />
    </div>
  );
}

function AuditPanel({
  events,
  onReload,
  busy,
}: {
  events: AuditEvent[];
  onReload: () => Promise<void>;
  busy: boolean;
}) {
  return (
    <section className="panel audit-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">NHẬT KÝ HOẠT ĐỘNG</span>
          <h3>Hoạt động gần đây</h3>
        </div>
        <button className="ghost" onClick={() => void onReload()} disabled={busy}>
          Làm mới nhật ký
        </button>
      </div>
      {events.length === 0 ? (
        <div className="empty-state">
          <strong>Chưa có sự kiện audit.</strong>
          <span>Hoạt động tài khoản và admin sẽ xuất hiện tại đây.</span>
        </div>
      ) : (
        <div className="audit-list">
          {events.slice(0, 50).map((event) => (
            <div className="audit-row" key={event.id}>
              <div>
                <strong>{event.event_type}</strong>
                <span>{event.detail || "Không có thông tin bổ sung"}</span>
              </div>
              <div className="audit-meta">
                <span className={event.status === "SUCCESS" ? "badge badge-ok" : "badge"}>
                  {auditStatusVi(event.status)}
                </span>
                <span>{event.account_id ? "Tài khoản #" + event.account_id : event.actor}</span>
                <span>{new Date(event.created_at).toLocaleString("vi-VN")}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
