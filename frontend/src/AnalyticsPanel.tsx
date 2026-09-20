import { useEffect, useMemo, useState } from "react";

import { api, TikTokAccount, TikTokAnalyticsReport } from "./api";

type Props = {
  accounts: TikTokAccount[];
};

type Range = 7 | 30 | 90;

export default function AnalyticsPanel({ accounts }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(accounts[0]?.id ?? null);
  const [days, setDays] = useState<Range>(30);
  const [report, setReport] = useState<TikTokAnalyticsReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selected = useMemo(
    () => accounts.find((account) => account.id === selectedId) ?? null,
    [accounts, selectedId],
  );

  useEffect(() => {
    if (selectedId === null && accounts.length > 0) {
      setSelectedId(accounts[0].id);
    } else if (selectedId !== null && !accounts.some((account) => account.id === selectedId)) {
      setSelectedId(accounts[0]?.id ?? null);
    }
  }, [accounts, selectedId]);

  useEffect(() => {
    if (selectedId !== null) void loadReport(selectedId, days);
    else setReport(null);
  }, [selectedId, days]);

  async function loadReport(accountId: number, range: Range) {
    setLoading(true);
    setError("");
    try {
      setReport(await api.tiktokAnalytics(accountId, range));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load analytics");
      setReport(null);
    } finally {
      setLoading(false);
    }
  }

  const followerPoints = report?.account_points
    .filter((point) => typeof point.follower_count === "number")
    .map((point) => ({
      value: point.follower_count as number,
      label: new Date(point.captured_at).toLocaleDateString(),
    })) ?? [];

  const canCollectAccountStats = Boolean(selected?.scopes.includes("user.info.stats"));
  const canCollectVideoStats = Boolean(selected?.scopes.includes("video.list"));

  return (
    <section className="panel analytics-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">ANALYTICS ENGINE</span>
          <h3>Account & video performance</h3>
        </div>
        {accounts.length > 0 && (
          <select
            className="video-account-select"
            value={selectedId ?? ""}
            onChange={(event) => setSelectedId(Number(event.target.value))}
          >
            {accounts.map((account) => (
              <option value={account.id} key={account.id}>
                {account.display_name || account.username || "Account #" + account.id}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="analytics-toolbar">
        <div className="range-tabs">
          {([7, 30, 90] as Range[]).map((range) => (
            <button
              className={days === range ? "range-active" : "ghost"}
              key={range}
              onClick={() => setDays(range)}
            >
              {range} days
            </button>
          ))}
        </div>
        <button
          className="ghost"
          disabled={loading || selectedId === null}
          onClick={() => selectedId !== null && loadReport(selectedId, days)}
        >
          {loading ? "Loading…" : "Refresh report"}
        </button>
      </div>

      {error && <div className="error global-error">{error}</div>}

      {!canCollectAccountStats && !canCollectVideoStats && selected && (
        <div className="setup-box">
          <strong>Historical analytics needs additional TikTok permissions</strong>
          <p>
            Enable <code>user.info.stats</code> for account growth and <code>video.list</code>
            for video performance. This panel never fabricates missing historical data.
          </p>
        </div>
      )}

      <div className="analytics-summary">
        <DeltaCard label="Followers" value={report?.account_deltas.followers} />
        <DeltaCard label="Following" value={report?.account_deltas.following} />
        <DeltaCard label="Likes" value={report?.account_deltas.likes} />
        <DeltaCard label="Videos" value={report?.account_deltas.videos} />
      </div>

      <div className="analytics-grid">
        <article className="analytics-chart-card">
          <div className="analytics-card-head">
            <div>
              <strong>Follower history</strong>
              <span>{report?.account_snapshot_count ?? 0} real snapshots</span>
            </div>
          </div>
          {followerPoints.length < 2 ? (
            <div className="analytics-empty">
              <strong>Not enough historical data yet.</strong>
              <span>
                At least two real snapshots are required before a growth line can be drawn.
              </span>
            </div>
          ) : (
            <MiniLineChart points={followerPoints} />
          )}
        </article>

        <article className="analytics-chart-card">
          <div className="analytics-card-head">
            <div>
              <strong>Top video growth</strong>
              <span>{report?.video_snapshot_count ?? 0} real metric snapshots</span>
            </div>
          </div>
          {!report || report.top_videos.length === 0 ? (
            <div className="analytics-empty">
              <strong>No tracked video growth yet.</strong>
              <span>Video metrics appear after at least two synchronized observations.</span>
            </div>
          ) : (
            <div className="top-video-list">
              {report.top_videos.slice(0, 8).map((video) => (
                <div className="top-video-row" key={video.video_id}>
                  {video.cover_image_url ? (
                    <img src={video.cover_image_url} alt="" loading="lazy" />
                  ) : (
                    <div className="top-video-placeholder">TT</div>
                  )}
                  <div>
                    <strong>{video.title || "TikTok video"}</strong>
                    <span>
                      {formatMetric(video.view_count)} views · {formatDelta(video.view_delta)}
                    </span>
                  </div>
                  {video.share_url && (
                    <a href={video.share_url} target="_blank" rel="noreferrer">Open</a>
                  )}
                </div>
              ))}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}

function DeltaCard({ label, value }: { label: string; value?: number | null }) {
  return (
    <div className="analytics-delta-card">
      <span>{label}</span>
      <strong>{formatDelta(value)}</strong>
    </div>
  );
}

function formatMetric(value?: number | null) {
  return typeof value === "number" ? value.toLocaleString() : "—";
}

function formatDelta(value?: number | null) {
  if (typeof value !== "number") return "—";
  if (value > 0) return "+" + value.toLocaleString();
  return value.toLocaleString();
}

function MiniLineChart({ points }: { points: { value: number; label: string }[] }) {
  const values = points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = Math.max(max - min, 1);
  const coords = points.map((point, index) => {
    const x = points.length === 1 ? 50 : (index / (points.length - 1)) * 100;
    const y = 92 - ((point.value - min) / spread) * 82;
    return x + "," + y;
  }).join(" ");

  return (
    <div className="mini-chart">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Follower growth chart">
        <polyline points={coords} fill="none" vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="mini-chart-legend">
        <span>{points[0].label}: {points[0].value.toLocaleString()}</span>
        <span>{points[points.length - 1].label}: {points[points.length - 1].value.toLocaleString()}</span>
      </div>
    </div>
  );
}
