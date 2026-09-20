import { useEffect, useMemo, useState } from "react";

import { api, PublishJob, PublishSchedule, TikTokAccount } from "./api";

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
      setError(err instanceof Error ? err.message : "Unable to load publishing schedule");
    }
  }

  async function cancel(job: PublishJob) {
    setBusyId(job.id);
    setError("");
    setNotice("");
    try {
      await api.cancelPublishJob(job.id);
      setNotice("Canceled scheduled job #" + job.id + ".");
      await loadSchedule();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to cancel scheduled job");
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
      setNotice("Retry queued for job #" + job.id + ".");
      await loadSchedule();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to retry publish job");
    } finally {
      setBusyId(null);
    }
  }

  async function reschedule(job: PublishJob) {
    const local = edits[job.id] || localInputValue(job.scheduled_at || job.next_attempt_at);
    if (!local) {
      setError("Choose a new local date and time first.");
      return;
    }
    const value = new Date(local);
    if (!Number.isFinite(value.getTime()) || value.getTime() <= Date.now() + 30_000) {
      setError("New scheduled time must be at least 30 seconds in the future.");
      return;
    }

    setBusyId(job.id);
    setError("");
    setNotice("");
    try {
      await api.reschedulePublishJob(job.id, value.toISOString());
      setNotice("Rescheduled job #" + job.id + ".");
      setEdits((current) => {
        const next = { ...current };
        delete next[job.id];
        return next;
      });
      await loadSchedule();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reschedule publish job");
    } finally {
      setBusyId(null);
    }
  }

  const jobs = report?.jobs ?? [];

  return (
    <section className="panel scheduler-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">PUBLISHING QUEUE</span>
          <h3>Publishing Schedule</h3>
        </div>
        <div className="scheduler-filters">
          <select
            value={accountId ?? ""}
            onChange={(event) =>
              setAccountId(event.target.value ? Number(event.target.value) : undefined)
            }
          >
            <option value="">All accounts</option>
            {accounts.map((account) => (
              <option value={account.id} key={account.id}>
                {account.display_name || account.username || "Account #" + account.id}
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
                {range} days
              </button>
            ))}
          </div>
          <button className="ghost" onClick={loadSchedule}>Refresh</button>
        </div>
      </div>

      <div className="scheduler-summary">
        <Summary label="Total" value={report?.total ?? 0} />
        <Summary label="Scheduled" value={report?.scheduled ?? 0} />
        <Summary label="Ready" value={report?.ready ?? 0} />
        <Summary label="Running" value={report?.running ?? 0} />
        <Summary label="Completed" value={report?.completed ?? 0} />
        <Summary label="Failed" value={report?.failed ?? 0} />
        <Summary label="Canceled" value={report?.canceled ?? 0} />
      </div>

      {notice && <div className="notice">{notice}</div>}
      {error && <div className="error global-error">{error}</div>}

      {jobs.length === 0 ? (
        <div className="empty-state">
          <strong>No scheduled or retry jobs in this window.</strong>
          <span>
            Use Direct Post Studio and enable Schedule to place a job on this queue.
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
                    #{job.id} · {job.media_type} ·{" "}
                    {account?.display_name || account?.username || "Account #" + job.account_id}
                  </strong>
                  <span>
                    {effectiveAt
                      ? new Date(effectiveAt).toLocaleString()
                      : "No scheduled time"}
                  </span>
                  <span>
                    Remote: {job.status} · Queue: {job.schedule_status} · Retry{" "}
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
                        Reschedule
                      </button>
                      <button
                        className="ghost danger"
                        disabled={busyId === job.id}
                        onClick={() => cancel(job)}
                      >
                        Cancel
                      </button>
                    </>
                  )}
                  {retryable && (
                    <button
                      className="ghost"
                      disabled={busyId === job.id}
                      onClick={() => retry(job)}
                    >
                      Retry
                    </button>
                  )}
                  {!editable && !retryable && (
                    <span className={"scheduler-state state-" + job.schedule_status.toLowerCase()}>
                      {job.schedule_status}
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
      <strong>{value.toLocaleString()}</strong>
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
