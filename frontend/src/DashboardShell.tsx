import { useEffect, useMemo, useState } from "react";

import AccountSidebar from "./AccountSidebar";
import AccountWorkspace, { AccountSection } from "./AccountWorkspace";
import SystemWorkspace from "./SystemWorkspace";
import { AuditEvent, ReadyStatus, TikTokAccount, TikTokConfigStatus } from "./api";

type WorkspaceMode = "account" | "system" | "events";

type Props = {
  username: string;
  health: string;
  ready: ReadyStatus;
  config: TikTokConfigStatus | null;
  accounts: TikTokAccount[];
  auditEvents: AuditEvent[];
  oauthNotice: string;
  error: string;
  busy: boolean;
  onConnect: () => void;
  onLogout: () => Promise<void>;
  onReload: () => Promise<void>;
  onSyncProfile: (id: number) => Promise<void>;
  onRefreshToken: (id: number) => Promise<void>;
  onDisconnect: (id: number) => Promise<void>;
};

export default function DashboardShell(props: Props) {
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(
    props.accounts[0]?.id ?? null,
  );
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>("account");
  const [accountSection, setAccountSection] = useState<AccountSection>("basic");

  useEffect(() => {
    setSelectedAccountId((current) => {
      if (current !== null && props.accounts.some((account) => account.id === current)) {
        return current;
      }
      return props.accounts[0]?.id ?? null;
    });
  }, [props.accounts]);

  const selectedAccount = useMemo(
    () => props.accounts.find((account) => account.id === selectedAccountId) ?? null,
    [props.accounts, selectedAccountId],
  );

  function selectAccount(id: number) {
    setSelectedAccountId(id);
    setWorkspaceMode("account");
    setAccountSection("basic");
  }

  return (
    <div className="app-layout-v2">
      <AccountSidebar
        accounts={props.accounts}
        selectedAccountId={workspaceMode === "account" ? selectedAccountId : null}
        onSelectAccount={selectAccount}
        onConnect={props.onConnect}
        onOpenSystem={() => setWorkspaceMode("system")}
        onOpenEvents={() => setWorkspaceMode("events")}
        onLogout={() => void props.onLogout()}
        connecting={props.busy}
      />
      <main className="workspace-shell">
        <WorkspaceTopbar
          health={props.health}
          ready={props.ready.status}
          environment={props.config?.environment || "sandbox"}
          username={props.username}
        />
        {props.oauthNotice && <div className="notice">{props.oauthNotice}</div>}
        {props.error && <div className="error global-error">{props.error}</div>}
        {workspaceMode === "account" ? (
          selectedAccount ? (
            <AccountWorkspace
              account={selectedAccount}
              section={accountSection}
              onSectionChange={setAccountSection}
              config={props.config}
              busy={props.busy}
              onSyncProfile={props.onSyncProfile}
              onRefreshToken={props.onRefreshToken}
              onReconnect={props.onConnect}
              onDisconnect={props.onDisconnect}
            />
          ) : (
            <NoAccount onConnect={props.onConnect} busy={props.busy} />
          )
        ) : (
          <SystemWorkspace
            mode={workspaceMode}
            accounts={props.accounts}
            auditEvents={props.auditEvents}
            onReload={props.onReload}
            busy={props.busy}
          />
        )}
      </main>
    </div>
  );
}

function WorkspaceTopbar({
  health,
  ready,
  environment,
  username,
}: {
  health: string;
  ready: string;
  environment: string;
  username: string;
}) {
  return (
    <header className="workspace-topbar">
      <div>
        <strong>Trung tâm quản lý tài khoản</strong>
        <span>Đăng nhập: {username}</span>
      </div>
      <div className="workspace-health">
        <span className={health === "ok" ? "badge badge-ok" : "badge"}>
          API: {health === "ok" ? "Hoạt động" : health}
        </span>
        <span className={ready === "ready" ? "badge badge-ok" : "badge"}>
          Hệ thống: {ready === "ready" ? "Sẵn sàng" : ready}
        </span>
        <span className="badge">Môi trường: {environment}</span>
      </div>
    </header>
  );
}

function NoAccount({ onConnect, busy }: { onConnect: () => void; busy: boolean }) {
  return (
    <section className="panel no-account-workspace">
      <div className="empty-state">
        <strong>Chưa có tài khoản TikTok nào được kết nối.</strong>
        <span>Kết nối tài khoản đầu tiên để sử dụng hồ sơ, video, analytics và Content Posting API.</span>
        <button onClick={onConnect} disabled={busy}>
          {busy ? "Đang xử lý…" : "+ Kết nối tài khoản"}
        </button>
      </div>
    </section>
  );
}
