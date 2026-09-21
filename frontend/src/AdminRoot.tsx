import { useEffect, useState } from "react";

import AdminLogin from "./AdminLogin";
import DashboardShell from "./DashboardShell";
import {
  api,
  AuditEvent,
  AuthStatus,
  ReadyStatus,
  TikTokAccount,
  TikTokConfigStatus,
} from "./api";

export default function AdminRoot() {
  const [auth, setAuth] = useState<AuthStatus>({ authenticated: false });
  const [checking, setChecking] = useState(true);
  const [health, setHealth] = useState("checking");
  const [ready, setReady] = useState<ReadyStatus>({ status: "checking" });
  const [config, setConfig] = useState<TikTokConfigStatus | null>(null);
  const [accounts, setAccounts] = useState<TikTokAccount[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function checkSession() {
    try {
      const result = await api.me();
      setAuth(result);
      return result.authenticated;
    } catch {
      setAuth({ authenticated: false });
      return false;
    } finally {
      setChecking(false);
    }
  }

  async function loadDashboard() {
    const [healthResult, readyResult, configResult, accountsResult, auditResult] =
      await Promise.allSettled([
        api.health(),
        api.ready(),
        api.tiktokConfig(),
        api.tiktokAccounts(),
        api.auditEvents(),
      ]);
    setHealth(healthResult.status === "fulfilled" ? healthResult.value.status : "offline");
    setReady(
      readyResult.status === "fulfilled" ? readyResult.value : { status: "not_ready" },
    );
    if (configResult.status === "fulfilled") setConfig(configResult.value);
    if (accountsResult.status === "fulfilled") setAccounts(accountsResult.value);
    if (auditResult.status === "fulfilled") setAuditEvents(auditResult.value);
  }

  useEffect(() => {
    void checkSession();
    const params = new URLSearchParams(window.location.search);
    const result = params.get("tiktok");
    if (result === "connected") setNotice("Kết nối tài khoản TikTok thành công.");
    if (result === "error") {
      setNotice(params.get("message") || "Kết nối tài khoản TikTok thất bại.");
    }
    if (result) window.history.replaceState({}, "", window.location.pathname);
  }, []);

  useEffect(() => {
    if (auth.authenticated) {
      void loadDashboard();
      return;
    }
    const timer = window.setInterval(() => void checkSession(), 2000);
    return () => window.clearInterval(timer);
  }, [auth.authenticated]);

  if (checking) {
    return (
      <main className="shell">
        <section className="panel">Đang kiểm tra phiên đăng nhập…</section>
      </main>
    );
  }

  if (!auth.authenticated) return <AdminLogin onLoggedIn={setAuth} />;

  async function connect() {
    if (!config?.configured) {
      setError("OAuth TikTok chưa được cấu hình.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await api.startTikTokOAuth(config.scopes);
      window.location.assign(result.authorize_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể bắt đầu cấp quyền TikTok");
      setBusy(false);
    }
  }

  async function syncProfile(id: number) {
    setBusy(true);
    setError("");
    try {
      await api.syncTikTokProfile(id);
      await loadDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đồng bộ hồ sơ thất bại");
    } finally {
      setBusy(false);
    }
  }

  async function refreshToken(id: number) {
    setBusy(true);
    setError("");
    try {
      await api.refreshTikTokAccount(id);
      await loadDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Làm mới token thất bại");
    } finally {
      setBusy(false);
    }
  }

  async function disconnect(id: number) {
    setBusy(true);
    setError("");
    try {
      await api.disconnectTikTokAccount(id);
      await loadDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ngắt kết nối thất bại");
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    await api.logout();
    setAuth({ authenticated: false });
    setConfig(null);
    setAccounts([]);
    setAuditEvents([]);
  }

  return (
    <DashboardShell
      username={auth.username || "admin"}
      health={health}
      ready={ready}
      config={config}
      accounts={accounts}
      auditEvents={auditEvents}
      oauthNotice={notice}
      error={error}
      busy={busy}
      onConnect={() => void connect()}
      onLogout={logout}
      onReload={loadDashboard}
      onSyncProfile={syncProfile}
      onRefreshToken={refreshToken}
      onDisconnect={disconnect}
    />
  );
}
