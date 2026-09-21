import { useEffect, useState } from "react";

import { api, ReviewPackageReport } from "./api";

export default function ReviewPackagePanel() {
  const [report, setReport] = useState<ReviewPackageReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void load();
  }, []);

  async function load() {
    setBusy(true);
    try {
      setReport(await api.reviewPackage());
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load review package");
    } finally {
      setBusy(false);
    }
  }

  async function copy(value: string, label: string) {
    try {
      await navigator.clipboard.writeText(value);
      setNotice(label + " copied.");
    } catch {
      setNotice("Copy failed. Select the value manually.");
    }
  }

  return (
    <section className="panel review-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">TIKTOK APP REVIEW</span>
          <h3>Production Review Package</h3>
        </div>
        <div className="review-head-actions">
          <span
            className={
              "readiness-overall " +
              (report?.status === "READY_FOR_REVIEW"
                ? "readiness-ready"
                : "readiness-blocked")
            }
          >
            {report?.status ?? "CHECKING"}
          </span>
          <button className="ghost" disabled={busy} onClick={load}>
            {busy ? "Checking…" : "Re-check"}
          </button>
        </div>
      </div>

      {notice && <div className="notice">{notice}</div>}
      {error && <div className="error global-error">{error}</div>}

      {report && (
        <>
          <div className="review-url-grid">
            <ReviewUrl label="Website" value={report.website_url} onCopy={copy} />
            <ReviewUrl label="Terms" value={report.terms_url} onCopy={copy} />
            <ReviewUrl label="Privacy" value={report.privacy_url} onCopy={copy} />
            <ReviewUrl label="OAuth redirect" value={report.oauth_redirect_url} onCopy={copy} />
            <ReviewUrl label="Webhook" value={report.webhook_url} onCopy={copy} />
          </div>

          <div className="review-products">
            <strong>Products represented in the package</strong>
            <div>
              {report.products.map((product) => (
                <span key={product}>{product}</span>
              ))}
            </div>
          </div>

          <div className="review-section-title">
            <div>
              <strong>Real-scope acceptance matrix</strong>
              <span>Code → app configuration → account grant → live evidence</span>
            </div>
          </div>

          <div className="review-table-wrap">
            <table className="review-table">
              <thead>
                <tr>
                  <th>Scope</th>
                  <th>Product</th>
                  <th>Feature</th>
                  <th>Code</th>
                  <th>Configured</th>
                  <th>Granted accounts</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {report.scope_matrix.map((item) => (
                  <tr key={item.scope}>
                    <td><code>{item.scope}</code></td>
                    <td>{item.product}</td>
                    <td>{item.feature}</td>
                    <td>
                      <span className={"review-state " + (item.code_implemented ? "check-pass" : "check-fail")}>
                        {item.code_implemented ? "PASS" : "FAIL"}
                      </span>
                    </td>
                    <td>{item.configured ? "Yes" : "No"}</td>
                    <td>{item.connected_accounts_with_scope}</td>
                    <td>
                      <span
                        className={
                          "review-state " +
                          (item.status === "PASS"
                            ? "check-pass"
                            : item.status === "BLOCKED"
                              ? "check-fail"
                              : "check-warn")
                        }
                      >
                        {item.status}
                      </span>
                      <details>
                        <summary>{item.evidence_routes.length} route(s)</summary>
                        <div className="review-routes">
                          {item.evidence_routes.map((route) => (
                            <code key={route}>{route}</code>
                          ))}
                        </div>
                      </details>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="review-section-title">
            <div>
              <strong>Review checks</strong>
              <span>PASS can be evidenced automatically; MANUAL must be confirmed in Developer Portal.</span>
            </div>
          </div>

          <div className="review-check-list">
            {report.checks.map((check) => (
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

          <div className="review-section-title">
            <div>
              <strong>Demo video plan</strong>
              <span>Maximum five review videos; show only scopes actually requested.</span>
            </div>
          </div>

          <ol className="review-demo-list">
            {report.demo_video_plan.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}

function ReviewUrl({
  label,
  value,
  onCopy,
}: {
  label: string;
  value: string;
  onCopy: (value: string, label: string) => Promise<void>;
}) {
  return (
    <article>
      <span>{label}</span>
      <code>{value || "Not configured"}</code>
      <button className="ghost" disabled={!value} onClick={() => void onCopy(value, label)}>
        Copy
      </button>
    </article>
  );
}
