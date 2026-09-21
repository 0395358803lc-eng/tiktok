import { useMemo, useState } from "react";

import { TikTokAccount } from "./api";
import { accountStatusVi } from "./vi";

type Props = {
  accounts: TikTokAccount[];
  selectedAccountId: number | null;
  onSelectAccount: (id: number) => void;
  onConnect: () => void;
  onOpenSystem: () => void;
  onOpenEvents: () => void;
  onLogout: () => void;
  connecting: boolean;
};

export default function AccountSidebar({
  accounts,
  selectedAccountId,
  onSelectAccount,
  onConnect,
  onOpenSystem,
  onOpenEvents,
  onLogout,
  connecting,
}: Props) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return accounts;
    return accounts.filter((account) =>
      [account.display_name, account.username, account.open_id]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(normalized)),
    );
  }, [accounts, query]);

  return (
    <aside className="account-sidebar">
      <div className="sidebar-brand">
        <div className="mark">TH</div>
        <div>
          <strong>TH Creator Manager</strong>
          <span>Quản lý tài khoản qua API chính thức</span>
        </div>
      </div>

      <div className="sidebar-section-head">
        <div>
          <span className="eyebrow">TÀI KHOẢN</span>
          <strong>Tài khoản đã kết nối</strong>
        </div>
        <span className="sidebar-count">{accounts.length}</span>
      </div>

      <button className="sidebar-connect" onClick={onConnect} disabled={connecting}>
        {connecting ? "Đang xử lý…" : "+ Kết nối tài khoản"}
      </button>

      <input
        className="sidebar-search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Tìm tên, username hoặc open_id"
        aria-label="Tìm tài khoản TikTok"
      />

      <div className="sidebar-account-list">
        {filtered.length === 0 ? (
          <div className="sidebar-empty">
            <strong>Không tìm thấy tài khoản</strong>
            <span>Thay đổi từ khóa tìm kiếm.</span>
          </div>
        ) : (
          filtered.map((account) => (
            <button
              key={account.id}
              className={
                selectedAccountId === account.id
                  ? "sidebar-account active"
                  : "sidebar-account"
              }
              onClick={() => onSelectAccount(account.id)}
            >
              {account.avatar_url ? (
                <img src={account.avatar_url} alt="" />
              ) : (
                <div className="sidebar-avatar-placeholder">TT</div>
              )}
              <div className="sidebar-account-copy">
                <strong>{account.display_name || "Tài khoản TikTok"}</strong>
                <span>{account.username ? "@" + account.username : "ID #" + account.id}</span>
                <span className={"sidebar-status status-" + account.status.toLowerCase()}>
                  {accountStatusVi(account.status)}
                </span>
              </div>
            </button>
          ))
        )}
      </div>

      <div className="sidebar-bottom">
        <button className="sidebar-nav-button" onClick={onOpenSystem}>⚙️ Hệ thống</button>
        <button className="sidebar-nav-button" onClick={onOpenEvents}>🔔 Sự kiện</button>
        <button className="sidebar-nav-button danger-text" onClick={onLogout}>🚪 Đăng xuất</button>
      </div>
    </aside>
  );
}
