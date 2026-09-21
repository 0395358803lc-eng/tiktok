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
      setError(err instanceof Error ? err.message : "Không thể tải hồ sơ review");
    } finally {
      setBusy(false);
    }
  }

  async function copy(value: string, label: string) {
    try {
      await navigator.clipboard.writeText(value);
      setNotice(label + " đã được sao chép.");
    } catch {
      setNotice("Sao chép thất bại. Hãy chọn giá trị và sao chép thủ công.");
    }
  }

  return (
    <section className="panel review-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">TIKTOK APP REVIEW</span>
          <h3>Hồ sơ chuẩn bị review</h3>
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
            {report?.status ?? "ĐANG KIỂM TRA"}
          </span>
          <button className="ghost" disabled={busy} onClick={load}>
            {busy ? "Đang kiểm tra…" : "Kiểm tra lại"}
          </button>
        </div>
      </div>

      {notice && <div className="notice">{notice}</div>}
      {error && <div className="error global-error">{error}</div>}

      {report && (
        <>
          <div className="review-url-grid">
            <ReviewUrl label="Website" value={report.website_url} onCopy={copy} />
            <ReviewUrl label="Điều khoản" value={report.terms_url} onCopy={copy} />
            <ReviewUrl label="Quyền riêng tư" value={report.privacy_url} onCopy={copy} />
            <ReviewUrl label="OAuth redirect" value={report.oauth_redirect_url} onCopy={copy} />
            <ReviewUrl label="Webhook" value={report.webhook_url} onCopy={copy} />
          </div>

          <div className="review-products">
            <strong>Các sản phẩm/API có trong hồ sơ</strong>
            <div>
              {report.products.map((product) => (
                <span key={product}>{product}</span>
              ))}
            </div>
          </div>

          <div className="review-section-title">
            <div>
              <strong>Ma trận nghiệm thu scope thật</strong>
              <span>Code → cấu hình ứng dụng → tài khoản cấp quyền → bằng chứng thật</span>
            </div>
          </div>

          <div className="review-table-wrap">
            <table className="review-table">
              <thead>
                <tr>
                  <th>Scope</th>
                  <th>Sản phẩm</th>
                  <th>Tính năng</th>
                  <th>Code</th>
                  <th>Đã cấu hình</th>
                  <th>Tài khoản đã cấp</th>
                  <th>Bằng chứng</th>
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
                    <td>{item.configured ? "Có" : "Không"}</td>
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
              <strong>Kiểm tra hồ sơ review</strong>
              <span>Mục ĐẠT được kiểm chứng tự động; mục THỦ CÔNG phải xác nhận trong Developer Portal.</span>
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
              <strong>Kế hoạch video demo</strong>
              <span>Tối đa 5 video review; chỉ trình bày các scope thực sự xin duyệt.</span>
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
      <code>{value || "Chưa cấu hình"}</code>
      <button className="ghost" disabled={!value} onClick={() => void onCopy(value, label)}>
        Copy
      </button>
    </article>
  );
}
