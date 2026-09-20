import { FormEvent, useEffect, useState } from "react";

import {
  api,
  AuthStatus,
  ReadyStatus,
  TikTokAccount,
  TikTokConfigStatus,
} from "./api";

export default function App() {
  const [auth, setAuth] = useState<AuthStatus>({ authenticated: false });
  const [ready, setReady] = useState<ReadyStatus>({ status: "checking" });
  const [health, setHealth] = useState("checking");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [tiktokConfig, setTikTokConfig] = useState<TikTokConfigStatus | null>(null);
  const [accounts, setAccounts] = useState<TikTokAccount[]>([]);
  const [oauthNotice, setOauthNotice] = useState("");
  const [actionBusy, setActionBusy] = useState(false);

  async function refreshFoundation() {
    const [meResult, healthResult, readyResult] = await Promise.allSettled([
      api.me(), api.health(), api.ready(),
    ]);
    if (meResult.status === "fulfilled") setAuth(meResult.value);
    setHealth(healthResult.status === "fulfilled" ? healthResult.value.status : "offline");
    setReady(readyResult.status === "fulfilled" ? readyResult.value : { status: "not_ready" });
    setLoading(false);
  }


  async function loadTikTok() {
    const [configResult, accountsResult] = await Promise.allSettled([
      api.tiktokConfig(),
      api.tiktokAccounts(),
    ]);
    if (configResult.status === "fulfilled") setTikTokConfig(configResult.value);
    if (accountsResult.status === "fulfilled") setAccounts(accountsResult.value);
  }

  useEffect(() => {
    void refreshFoundation();
    const params = new URLSearchParams(window.location.search);
    const result = params.get("tiktok");
    if (result === "connected") setOauthNotice("TikTok account connected successfully.");
    if (result === "error") setOauthNotice(params.get("message") || "TikTok connection failed.");
    if (result) window.history.replaceState({}, "", window.location.pathname);
  }, []);

  useEffect(() => {
    if (auth.authenticated) void loadTikTok();
  }, [auth.authenticated]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      const result = await api.login(
        String(data.get("username") ?? ""),
        String(data.get("password") ?? ""),
      );
      setAuth(result);
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }


  async function logout() {
    await api.logout();
    setAuth({ authenticated: false });
    setTikTokConfig(null);
    setAccounts([]);
  }

  async function connectTikTok() {
    setActionBusy(true);
    setError("");
    try {
      const result = await api.startTikTokOAuth();
      window.location.assign(result.authorize_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start TikTok OAuth");
      setActionBusy(false);
    }
  }

  async function refreshAccount(id: number) {
    setActionBusy(true);
    setError("");
    try {
      await api.refreshTikTokAccount(id);
      await loadTikTok();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Token refresh failed");
    } finally {
      setActionBusy(false);
    }
  }

  async function syncProfile(id: number) {
    setActionBusy(true);
    setError("");
    try {
      await api.syncTikTokProfile(id);
      await loadTikTok();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Profile sync failed");
    } finally {
      setActionBusy(false);
    }
  }

  async function disconnectAccount(id: number) {
    setActionBusy(true);
    setError("");
    try {
      await api.disconnectTikTokAccount(id);
      await loadTikTok();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Disconnect failed");
    } finally {
      setActionBusy(false);
    }
  }


  if (loading) {
    return <main className="shell"><section className="panel">Checking services…</section></main>;
  }

  return (
    <main className="shell">
      <header className="brand">
        <div className="mark">TH</div>
        <div>
          <h1>TH TikTok Manager</h1>
          <p>Multi-account API control plane</p>
        </div>
      </header>

      {!auth.authenticated ? (
        <section className="panel login-panel">
          <div>
            <span className="eyebrow">ADMIN ACCESS</span>
            <h2>Sign in to the control plane</h2>
            <p>Credentials are verified by the backend and the session stays server-backed.</p>
          </div>
          <form onSubmit={submit}>
            <label>
              Username
              <input name="username" autoComplete="username" required defaultValue="admin" />
            </label>
            <label>
              Password
              <input name="password" type="password" autoComplete="current-password" required />
            </label>
            {error && <div className="error">{error}</div>}
            <button type="submit">Sign in</button>
          </form>
        </section>
      ) : (
        <>
          <section className="hero panel">
            <div>
              <span className="eyebrow">BATCH B — TIKTOK OAUTH</span>
              <h2>OAuth control plane is ready.</h2>
              <p>
                Signed in as <strong>{auth.username}</strong>. TikTok accounts connect through
                official OAuth and server-side token storage.
              </p>
            </div>
            <button className="ghost" onClick={logout}>Sign out</button>
          </section>

          <section className="grid">
            <StatusCard title="API" value={health} ok={health === "ok"} />
            <StatusCard title="Readiness" value={ready.status} ok={ready.status === "ready"} />
            <StatusCard
              title="PostgreSQL"
              value={ready.checks?.database ? "connected" : "unavailable"}
              ok={Boolean(ready.checks?.database)}
            />
            <StatusCard
              title="Cache"
              value={ready.checks?.cache ? "connected" : "unavailable"}
              ok={Boolean(ready.checks?.cache)}
            />
          </section>

          {oauthNotice && <div className="notice">{oauthNotice}</div>}
          {error && <div className="error global-error">{error}</div>}

          <section className="panel oauth-panel">
            <div className="section-head">
              <div>
                <span className="eyebrow">TIKTOK LOGIN KIT</span>
                <h3>Account connections</h3>
              </div>
              <button
                onClick={connectTikTok}
                disabled={!tiktokConfig?.configured || actionBusy}
              >
                {actionBusy ? "Working…" : "+ Connect TikTok"}
              </button>
            </div>

            <div className="config-strip">
              <StatusBadge
                ok={Boolean(tiktokConfig?.configured)}
                label={tiktokConfig?.configured ? "OAuth configured" : "OAuth not configured"}
              />
              <span>
                Scopes: {tiktokConfig?.scopes.join(", ") || "user.info.basic"}
              </span>
            </div>

            {!tiktokConfig?.configured && (
              <div className="setup-box">
                <strong>Developer credentials required</strong>
                <p>
                  Add TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET and an HTTPS
                  TIKTOK_REDIRECT_URI to the server environment, then restart the backend.
                </p>
                <code>
                  {tiktokConfig?.redirect_uri || "https://your-domain/api/tiktok/oauth/callback"}
                </code>
              </div>
            )}


            {accounts.length === 0 ? (
              <div className="empty-state">
                <strong>No TikTok accounts connected yet.</strong>
                <span>Once OAuth is configured, connect each account separately.</span>
              </div>
            ) : (
              <div className="accounts-list">
                {accounts.map((account) => (
                  <article className="account-row" key={account.id}>
                    <div className="account-identity">
                      {account.avatar_url ? (
                        <img className="account-avatar" src={account.avatar_url} alt="" />
                      ) : (
                        <div className="account-avatar placeholder">TT</div>
                      )}
                      <div>
                        <strong>{account.display_name || "TikTok account"}</strong>
                        <span>{account.open_id}</span>
                        <span>{account.scopes.join(", ")}</span>
                      </div>
                    </div>
                    <div className="account-meta">
                      <StatusBadge
                        ok={account.status === "CONNECTED"}
                        label={account.status}
                      />
                      <span>
                        Access expires {new Date(account.access_token_expires_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="account-actions">
                      <button
                        className="ghost"
                        disabled={actionBusy || account.status === "REVOKED"}
                        onClick={() => syncProfile(account.id)}
                      >
                        Sync profile
                      </button>
                      <button
                        className="ghost"
                        disabled={actionBusy || account.status === "REVOKED"}
                        onClick={() => refreshAccount(account.id)}
                      >
                        Refresh token
                      </button>
                      <button
                        className="danger"
                        disabled={actionBusy || account.status === "REVOKED"}
                        onClick={() => disconnectAccount(account.id)}
                      >
                        Disconnect
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="panel next">
            <span className="eyebrow">IMPLEMENTATION STATUS</span>
            <h3>OAuth connected — profile synchronization enabled</h3>
            <p>
              Connected accounts use server-side encrypted tokens. Profile sync retrieves the
              authorized TikTok display name and avatar without exposing raw credentials.
            </p>
          </section>
        </>
      )}
    </main>
  );
}

function StatusCard({ title, value, ok }: { title: string; value: string; ok: boolean }) {
  return (
    <article className="status-card">
      <div className={ok ? "dot ok" : "dot"} />
      <span>{title}</span>
      <strong>{value}</strong>
    </article>
  );
}

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return <span className={ok ? "badge badge-ok" : "badge"}>{label}</span>;
}
