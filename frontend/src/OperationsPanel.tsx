import { useEffect, useMemo, useState } from "react";

import {
  api,
  BulkOperationResponse,
  OperationsSummary,
  ProductionReadinessReport,
  TikTokAccount,
} from "./api";
import { accountStatusVi, bulkActionVi, checkStatusVi, healthStatusVi, readinessStatusVi } from "./vi";

type Props = {
  accounts: TikTokAccount[];
  onChanged: () => Promise<void>;
};

type BulkAction = "REFRESH_TOKENS" | "SYNC_PROFILE" | "SYNC_VIDEOS";

export default function OperationsPanel({ accounts, onChanged }: Props) {
  const [summary, setSummary] = useState<OperationsSummary | null>(null);
  const [readiness, setReadiness] = useState<ProductionReadinessReport | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [bulkAction, setBulkAction] = useState<BulkAction>("REFRESH_TOKENS");
  const [bulkResult, setBulkResult] = useState<BulkOperationResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const accountMap = useMemo(
    () => new Map(accounts.map((account) => [account.id, account])),
    [accounts],
  );

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 15000);
    return () => window.clearInterval(timer);
  }, []);

  async function load() {
    try {
      const [ops, gate] = await Promise.all([
        api.operationsSummary(),
        api.productionReadiness(),
      ]);
      setSummary(ops);
      setReadiness(gate);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải bảng điều hành hệ thống");
    }
  }

  function toggleAccount(id: number) {
    setSelected((current) =>
      current.includes(id)
        ? current.filter((value) => value !== id)
        : [...current, id],
    );
  }

  function toggleAll() {
    const ids = summary?.accounts.map((row) => row.account_id) ?? [];
    setSelected((current) => (current.length === ids.length ? [] : ids));
  }

  async function runBulk() {
    if (selected.length === 0) {
      setError("Hãy chọn ít nhất một tài khoản TikTok.");
      return;
    }

    setBusy(true);
    setError("");
    setBulkResult(null);
    try {
      const result = await api.bulkOperation(bulkAction, selected);
      setBulkResult(result);
      await Promise.all([load(), onChanged()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Thao tác hàng loạt thất bại");
    } finally {
      setBusy(false);
    }
  }

  const rows = summary?.accounts ?? [];

  return (
    <>
      <section className="panel operations-panel">
        <div className="section-head">
          <div>
            <span className="eyebrow">VẬN HÀNH NHIỀU TÀI KHOẢN</span>
            <h3>Trung tâm điều hành</h3>
          </div>
          <button className="ghost" disabled={busy} onClick={load}>
            {busy ? "Đang xử lý…" : "Làm mới bảng điều hành"}
          </button>
        </div>

        <div className="ops-summary-grid">
          <OpsMetric label="Tài khoản" value={summary?.accounts_total ?? 0} />
          <OpsMetric label="Đã kết nối" value={summary?.connected_accounts ?? 0} />
          <OpsMetric label="Cần chú ý" value={summary?.issue_accounts ?? 0} />
          <OpsMetric label="Cần cấp lại quyền" value={summary?.reauth_accounts ?? 0} />
          <OpsMetric label="Đã lên lịch" value={summary?.scheduled_posts ?? 0} />
          <OpsMetric label="Đang chạy" value={summary?.running_posts ?? 0} />
          <OpsMetric label="Bài đăng lỗi" value={summary?.failed_posts ?? 0} />
          <OpsMetric
            label="Lỗi Webhook"
            value={summary?.error_webhooks ?? 0}
          />
        </div>

        <div className="bulk-toolbar">
          <label className="check-label">
            <input
              type="checkbox"
              checked={rows.length > 0 && selected.length === rows.length}
              onChange={toggleAll}
            />
            Chọn tất cả
          </label>
          <select
            value={bulkAction}
            onChange={(event) => setBulkAction(event.target.value as BulkAction)}
          >
            <option value="REFRESH_TOKENS">Làm mới token</option>
            <option value="SYNC_PROFILE">Đồng bộ hồ sơ</option>
            <option value="SYNC_VIDEOS">Đồng bộ video mới nhất</option>
          </select>
          <button disabled={busy || selected.length === 0} onClick={runBulk}>
            {busy ? "Đang chạy…" : "Chạy trên " + selected.length + " tài khoản"}
          </button>
        </div>

        {error && <div className="error global-error">{error}</div>}

        {bulkResult && (
          <div className="bulk-result">
            <strong>
              {bulkActionVi(bulkResult.action)}: {bulkResult.succeeded} thành công / {bulkResult.failed} thất bại
            </strong>
            <div>
              {bulkResult.results.map((item) => (
                <span
                  className={item.ok ? "bulk-ok" : "bulk-fail"}
                  key={item.account_id}
                >
                  #{item.account_id}: {item.detail}
                </span>
              ))}
            </div>
          </div>
        )}

        {rows.length === 0 ? (
          <div className="empty-state">
            <strong>Chưa có tài khoản TikTok nào được kết nối.</strong>
            <span>Kết nối tài khoản để hiển thị dữ liệu vận hành.</span>
          </div>
        ) : (
          <div className="ops-table-wrap">
            <table className="ops-table">
              <thead>
                <tr>
                  <th />
                  <th>Tài khoản</th>
                  <th>Sức khỏe</th>
                  <th>Quyền</th>
                  <th>Token truy cập</th>
                  <th>Token làm mới</th>
                  <th>Đồng bộ hồ sơ</th>
                  <th>Video</th>
                  <th>Đăng bài</th>
                  <th>Vấn đề</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const account = accountMap.get(row.account_id);
                  return (
                    <tr key={row.account_id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selected.includes(row.account_id)}
                          onChange={() => toggleAccount(row.account_id)}
                        />
                      </td>
                      <td>
                        <strong>
                          {row.display_name ||
                            row.username ||
                            account?.display_name ||
                            "Tài khoản #" + row.account_id}
                        </strong>
                        <span>#{row.account_id} · {accountStatusVi(row.status)}</span>
                      </td>
                      <td>
                        <span className={"ops-health health-" + row.health.toLowerCase()}>
                          {healthStatusVi(row.health)}
                        </span>
                      </td>
                      <td>
                        <strong>{row.scopes.length}</strong>
                        <span>
                          {row.missing_configured_scopes.length
                            ? row.missing_configured_scopes.length + " thiếu"
                            : "Đầy đủ"}
                        </span>
                      </td>
                      <td>
                        <strong>{formatMinutes(row.access_token_minutes_left)}</strong>
                        <span>{new Date(row.access_token_expires_at).toLocaleString()}</span>
                      </td>
                      <td>
                        <strong>{row.refresh_token_days_left}d</strong>
                        <span>{new Date(row.refresh_token_expires_at).toLocaleDateString()}</span>
                      </td>
                      <td>
                        <strong>
                          {row.profile_age_hours == null
                            ? "Chưa từng"
                            : row.profile_age_hours.toFixed(1) + " giờ trước"}
                        </strong>
                      </td>
                      <td>
                        <strong>{row.stored_videos}</strong>
                      </td>
                      <td>
                        <strong>
                          {row.scheduled_posts} đã lên lịch · {row.running_posts} đang chạy
                        </strong>
                        <span>
                          {row.failed_posts} thất bại posts · {row.failed_drafts} thất bại drafts
                        </span>
                      </td>
                      <td>
                        {row.issues.length === 0 ? (
                          <span className="ops-no-issues">Không có vấn đề</span>
                        ) : (
                          <details>
                            <summary>{row.issues.length} vấn đề</summary>
                            <div className="ops-issues">
                              {row.issues.map((issue) => (
                                <span key={issue}>{issue}</span>
                              ))}
                            </div>
                          </details>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel readiness-panel">
        <div className="section-head">
          <div>
            <span className="eyebrow">CỔNG KIỂM TRA PRODUCTION</span>
            <h3>Mức sẵn sàng Production</h3>
          </div>
          <span
            className={
              "readiness-overall readiness-" +
              (readiness?.status === "READY" ? "ready" : "blocked")
            }
          >
            {readinessStatusVi(readiness?.status ?? "CHECKING")}
          </span>
        </div>

        <div className="readiness-summary">
          <OpsMetric label="ĐẠT" value={readiness?.pass_count ?? 0} />
          <OpsMetric label="CẢNH BÁO" value={readiness?.warn_count ?? 0} />
          <OpsMetric label="LỖI" value={readiness?.fail_count ?? 0} />
        </div>

        <div className="readiness-list">
          {(readiness?.checks ?? []).map((check) => (
            <article className="readiness-row" key={check.key}>
              <span className={"readiness-check check-" + check.status.toLowerCase()}>
                {checkStatusVi(check.status)}
              </span>
              <div>
                <strong>{check.label}</strong>
                <span>{check.detail}</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function OpsMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="ops-metric">
      <span>{label}</span>
      <strong>{value.toLocaleString()}</strong>
    </div>
  );
}

function formatMinutes(value: number) {
  if (value < 0) return "Đã hết hạn";
  if (value < 60) return value + "m";
  if (value < 1440) return Math.floor(value / 60) + "h";
  return Math.floor(value / 1440) + "d";
}
