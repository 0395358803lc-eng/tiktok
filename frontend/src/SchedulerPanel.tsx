import { useEffect, useMemo, useState } from "react";

import { api, PublishJob, PublishSchedule, TikTokAccount } from "./api";
import { jobStatusVi, mediaTypeVi } from "./vi";

type Props = {
  accounts: TikTokAccount[];
};

type Range = 7 | 30;

export default function SchedulerPanel({ accounts }: Props) {
  const [days, setDays] = useState<Range>(7);
  const [accountId, setAccountId] = useState<number | undefined>(undefined);
  const [report, setReport] = useState<PublishSchedule | null>(null);
  const [edits, setEdits] = useState<Record<number, string>>({});
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const accountMap = useMemo(
    () => new Map(accounts.map((account) => [account.id, account])),
    [accounts],
  );

  useEffect(() => {
    void loadSchedule();
    const timer = window.setInterval(() => void loadSchedule(), 15000);
    return () => window.clearInterval(timer);
  }, [days, accountId]);

  async function loadSchedule() {
    try {
      setReport(await api.publishSchedule(days, accountId));
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải lịch đăng");
    }
  }

  async function cancel(job: PublishJob) {
    setBusyId(job.id);
    setError("");
    setNotice("");
    try {
      await api.cancelPublishJob(job.id);
      setNotice("Đã hủy tác vụ đã lên lịch #" + job.id + ".");
      await loadSchedule();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể hủy tác vụ đã lên lịch");
    } finally {
      setBusyId(null);
    }
  }

  async function retry(job: PublishJob) {
    setBusyId(job.id);
    setError("");
    setNotice("");
    try {
      await api.retryPublishJob(job.id);
      setNotice("Đã đưa yêu cầu thử lại cho tác vụ #" + job.id + " vào hàng đợi.");
      await loadSchedule();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể thử lại tác vụ đăng");
    } finally {
      setBusyId(null);
    }
  }

  async function reschedule(job: PublishJob) {
    const local = edits[job.id] || localInputValue(job.scheduled_at || job.next_attempt_at);
    if (!local) {
      setError("Hãy chọn ngày giờ địa phương mới trước.");
      return;
    }
    const value = new Date(local);
    if (!Number.isFinite(value.getTime()) || value.getTime() <= Date.now() + 30_000) {
      setError("Thời gian mới phải cách hiện tại ít nhất 30 giây.");
      return;
    }

    setBusyId(job.id);
    setError("");
    setNotice("");
    try {
      await api.reschedulePublishJob(job.id, value.toISOString());
      setNotice("Đã đổi lịch tác vụ #" + job.id + ".");
      setEdits((current) => {
        const next = { ...current };
        delete next[job.id];
        return next;
      });
      await loadSchedule();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể đổi lịch tác vụ đăng");
    } finally {
      setBusyId(null);
    }
  }

  const jobs = report?.jobs ?? [];

  return (
    <section className="panel scheduler-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">HÀNG ĐỢI ĐĂNG BÀI</span>
          <h3>Lịch đăng bài</h3>
        </div>
        <div className="scheduler-filters">
          <select
            hidden={accounts.length <= 1}
            value={accountId ?? ""}
            onChange={(event) =>
              setAccountId(event.target.value ? Number(event.target.value) : undefined)
            }
          >
            <option value="">Tất cả tài khoản</option>
            {accounts.map((account) => (
              <option value={account.id} key={account.id}>
                {account.display_name || account.username || "Tài khoản #" + account.id}
              </option>
            ))}
          </select>
          <div className="range-tabs">
            {([7, 30] as Range[]).map((range) => (
              <button
                key={range}
                className={days === range ? "range-active" : "ghost"}
                onClick={() => setDays(range)}
              >
                {range} ngày
              </button>
            ))}
          </div>
          <button className="ghost" onClick={loadSchedule}>Làm mới</button>
        </div>
      </div>

      <div className="scheduler-summary">
        <Summary label="Tổng" value={report?.total ?? 0} />
        <Summary label="Đã lên lịch" value={report?.scheduled ?? 0} />
        <Summary label="Sẵn sàng" value={report?.ready ?? 0} />
        <Summary label="Đang chạy" value={report?.running ?? 0} />
        <Summary label="Hoàn tất" value={report?.completed ?? 0} />
        <Summary label="Thất bại" value={report?.failed ?? 0} />
        <Summary label="Đã hủy" value={report?.canceled ?? 0} />
      </div>

      {notice && <div className="notice">{notice}</div>}
      {error && <div className="error global-error">{error}</div>}

      {jobs.length === 0 ? (
        <div className="empty-state">
          <strong>Không có tác vụ lên lịch hoặc thử lại trong khoảng thời gian này.</strong>
          <span>
            Dùng trình đăng trực tiếp và bật Lên lịch để đưa tác vụ vào hàng đợi này.
          </span>
        </div>
      ) : (
        <div className="scheduler-list">
          {jobs.map((job) => {
            const account = accountMap.get(job.account_id);
            const editable =
              !job.publish_id && ["SCHEDULED", "READY"].includes(job.schedule_status);
            const retryable =
              !job.publish_id &&
              job.schedule_status === "FAILED" &&
              job.retry_count < job.max_retries;
            const effectiveAt = job.next_attempt_at || job.scheduled_at;

            return (
              <article className="scheduler-row" key={job.id}>
                <div className="scheduler-row-main">
                  <strong>
                    #{job.id} · {mediaTypeVi(job.media_type)} ·{" "}
                    {account?.display_name || account?.username || "Tài khoản #" + job.account_id}
                  </strong>
                  <span>
                    {effectiveAt
                      ? new Date(effectiveAt).toLocaleString("vi-VN")
                      : "Chưa có thời gian lên lịch"}
                  </span>
                  <span>
                    TikTok: {jobStatusVi(job.status)} · Hàng đợi: {jobStatusVi(job.schedule_status)} · Thử lại{" "}
                    {job.retry_count}/{job.max_retries}
                  </span>
                  {job.fail_reason && (
                    <span className="draft-failure">{job.fail_reason}</span>
                  )}
                </div>

                <div className="scheduler-row-actions">
                  {editable && (
                    <>
                      <input
                        type="datetime-local"
                        value={
                          edits[job.id] ??
                          localInputValue(job.scheduled_at || job.next_attempt_at)
                        }
                        onChange={(event) =>
                          setEdits((current) => ({
                            ...current,
                            [job.id]: event.target.value,
                          }))
                        }
                      />
                      <button
                        className="ghost"
                        disabled={busyId === job.id}
                        onClick={() => reschedule(job)}
                      >
                        Đổi lịch
                      </button>
                      <button
                        className="ghost danger"
                        disabled={busyId === job.id}
                        onClick={() => cancel(job)}
                      >
                        Hủy
                      </button>
                    </>
                  )}
                  {retryable && (
                    <button
                      className="ghost"
                      disabled={busyId === job.id}
                      onClick={() => retry(job)}
                    >
                      Thử lại
                    </button>
                  )}
                  {!editable && !retryable && (
                    <span className={"scheduler-state state-" + job.schedule_status.toLowerCase()}>
                      {jobStatusVi(job.schedule_status)}
                    </span>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function Summary({ label, value }: { label: string; value: number }) {
  return (
    <div className="scheduler-summary-card">
      <span>{label}</span>
      <strong>{value.toLocaleString("vi-VN")}</strong>
    </div>
  );
}

function localInputValue(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "";
  const shifted = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return shifted.toISOString().slice(0, 16);
}
