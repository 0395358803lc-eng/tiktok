import { FormEvent, useState } from "react";

import { api, AuthStatus } from "./api";

export default function AdminLogin({
  onLoggedIn,
}: {
  onLoggedIn: (status: AuthStatus) => void;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    setError("");
    try {
      const result = await api.login(
        String(data.get("username") ?? ""),
        String(data.get("password") ?? ""),
      );
      onLoggedIn(result);
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập thất bại");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <header className="brand">
        <div className="mark">TH</div>
        <div>
          <h1>TH TikTok Manager</h1>
          <p>Trung tâm quản lý tài khoản qua API chính thức</p>
        </div>
      </header>

      <section className="panel login-panel">
        <div>
          <span className="eyebrow">TRUY CẬP QUẢN TRỊ</span>
          <h2>Đăng nhập hệ thống quản trị</h2>
          <p>
            Thông tin đăng nhập được backend xác thực và phiên làm việc được lưu phía máy chủ.
          </p>
        </div>

        <form onSubmit={submit}>
          <label>
            Tên đăng nhập
            <input name="username" autoComplete="username" required />
          </label>
          <label>
            Mật khẩu
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy}>
            {busy ? "Đang đăng nhập…" : "Đăng nhập"}
          </button>
        </form>
      </section>
    </main>
  );
}
