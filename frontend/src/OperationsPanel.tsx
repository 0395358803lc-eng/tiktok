import { useEffect, useMemo, useState } from "react";

import {
  api,
  BulkOperationResponse,
  OperationsSummary,
  ProductionReadinessReport,
  TikTokAccount,
} from "./api";

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
      setError(err instanceof Error ? err.message : "Unable to load operations dashboard");
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
      setError("Select at least one TikTok account.");
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
      setError(err instanceof Error ? err.message : "Bulk operation failed");
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
            <span className="eyebrow">MULTI-ACCOUNT OPERATIONS</span>
            <h3>Operations Control Center</h3>
          </div>
          <button className="ghost" disabled={busy} onClick={load}>
            {busy ? "Working…" : "Refresh dashboard"}
          </button>
        </div>

        <div className="ops-summary-grid">
          <OpsMetric label="Accounts" value={summary?.accounts_total ?? 0} />
          <OpsMetric label="Connected" value={summary?.connected_accounts ?? 0} />
          <OpsMetric label="Need attention" value={summary?.issue_accounts ?? 0} />
          <OpsMetric label="Re-auth" value={summary?.reauth_accounts ?? 0} />
          <OpsMetric label="Scheduled" value={summary?.scheduled_posts ?? 0} />
          <OpsMetric label="Running" value={summary?.running_posts ?? 0} />
          <OpsMetric label="Failed posts" value={summary?.failed_posts ?? 0} />
          <OpsMetric
            label="Webhook errors"
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
            Select all
          </label>
          <select
            value={bulkAction}
            onChange={(event) => setBulkAction(event.target.value as BulkAction)}
          >
            <option value="REFRESH_TOKENS">Refresh tokens</option>
            <option value="SYNC_PROFILE">Sync profiles</option>
            <option value="SYNC_VIDEOS">Sync latest videos</option>
          </select>
          <button disabled={busy || selected.length === 0} onClick={runBulk}>
            {busy ? "Running…" : "Run on " + selected.length + " account(s)"}
          </button>
        </div>

        {error && <div className="error global-error">{error}</div>}

        {bulkResult && (
          <div className="bulk-result">
            <strong>
              {bulkResult.action}: {bulkResult.succeeded} succeeded / {bulkResult.failed} failed
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
            <strong>No TikTok account is connected.</strong>
            <span>Connect an account to populate the operations dashboard.</span>
          </div>
        ) : (
          <div className="ops-table-wrap">
            <table className="ops-table">
              <thead>
                <tr>
                  <th />
                  <th>Account</th>
                  <th>Health</th>
                  <th>Scopes</th>
                  <th>Access token</th>
                  <th>Refresh token</th>
                  <th>Profile sync</th>
                  <th>Videos</th>
                  <th>Publishing</th>
                  <th>Issues</th>
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
                            "Account #" + row.account_id}
                        </strong>
                        <span>#{row.account_id} · {row.status}</span>
                      </td>
                      <td>
                        <span className={"ops-health health-" + row.health.toLowerCase()}>
                          {row.health}
                        </span>
                      </td>
                      <td>
                        <strong>{row.scopes.length}</strong>
                        <span>
                          {row.missing_configured_scopes.length
                            ? row.missing_configured_scopes.length + " missing"
                            : "Complete"}
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
                            ? "Never"
                            : row.profile_age_hours.toFixed(1) + "h ago"}
                        </strong>
                      </td>
                      <td>
                        <strong>{row.stored_videos}</strong>
                      </td>
                      <td>
                        <strong>
                          {row.scheduled_posts} scheduled · {row.running_posts} running
                        </strong>
                        <span>
                          {row.failed_posts} failed posts · {row.failed_drafts} failed drafts
                        </span>
                      </td>
                      <td>
                        {row.issues.length === 0 ? (
                          <span className="ops-no-issues">No issues</span>
                        ) : (
                          <details>
                            <summary>{row.issues.length} issue(s)</summary>
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
            <span className="eyebrow">PRODUCTION GATE</span>
            <h3>Production Readiness</h3>
          </div>
          <span
            className={
              "readiness-overall readiness-" +
              (readiness?.status === "READY" ? "ready" : "blocked")
            }
          >
            {readiness?.status ?? "CHECKING"}
          </span>
        </div>

        <div className="readiness-summary">
          <OpsMetric label="PASS" value={readiness?.pass_count ?? 0} />
          <OpsMetric label="WARN" value={readiness?.warn_count ?? 0} />
          <OpsMetric label="FAIL" value={readiness?.fail_count ?? 0} />
        </div>

        <div className="readiness-list">
          {(readiness?.checks ?? []).map((check) => (
            <article className="readiness-row" key={check.key}>
              <span className={"readiness-check check-" + check.status.toLowerCase()}>
                {check.status}
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
  if (value < 0) return "Expired";
  if (value < 60) return value + "m";
  if (value < 1440) return Math.floor(value / 60) + "h";
  return Math.floor(value / 1440) + "d";
}
