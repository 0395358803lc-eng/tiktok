export type AuthStatus = {
  authenticated: boolean;
  username?: string | null;
};

export type ReadyStatus = {
  status: string;
  checks?: Record<string, boolean>;
};

export type TikTokConfigStatus = {
  configured: boolean;
  scopes: string[];
  redirect_uri?: string | null;
};

export type TikTokAccount = {
  id: number;
  open_id: string;
  union_id?: string | null;
  display_name?: string | null;
  avatar_url?: string | null;
  scopes: string[];
  status: string;
  access_token_expires_at: string;
  refresh_token_expires_at: string;
  last_token_refresh_at?: string | null;
  profile_synced_at?: string | null;
};

type OAuthStart = { authorize_url: string };


async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    const detail = typeof body.detail === "string" ? body.detail : "Request failed";
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const api = {
  me: () => json<AuthStatus>("/api/auth/me"),
  health: () => json<{ status: string }>("/health"),
  ready: () => json<ReadyStatus>("/ready"),
  login: (username: string, password: string) =>
    json<AuthStatus>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: () => json<AuthStatus>("/api/auth/logout", { method: "POST" }),
  tiktokConfig: () => json<TikTokConfigStatus>("/api/tiktok/config"),
  tiktokAccounts: () => json<TikTokAccount[]>("/api/tiktok/accounts"),
  startTikTokOAuth: () =>
    json<OAuthStart>("/api/tiktok/oauth/start", { method: "POST" }),
  refreshTikTokAccount: (id: number) =>
    json<TikTokAccount>(`/api/tiktok/accounts/${id}/refresh`, { method: "POST" }),
  syncTikTokProfile: (id: number) =>
    json<TikTokAccount>(`/api/tiktok/accounts/${id}/sync-profile`, { method: "POST" }),
  disconnectTikTokAccount: (id: number) =>
    json<TikTokAccount>(`/api/tiktok/accounts/${id}/disconnect`, { method: "POST" }),
};
