export type AuthStatus = {
  authenticated: boolean;
  username?: string | null;
};

export type ReadyStatus = {
  status: string;
  checks?: Record<string, boolean>;
};

export type TikTokScopeCapability = {
  scope: string;
  label: string;
  description: string;
  configured: boolean;
};

export type TikTokConfigStatus = {
  configured: boolean;
  environment: string;
  scopes: string[];
  scope_capabilities: TikTokScopeCapability[];
  redirect_uri?: string | null;
};

export type TikTokAccount = {
  id: number;
  open_id: string;
  union_id?: string | null;
  display_name?: string | null;
  avatar_url?: string | null;
  username?: string | null;
  bio_description?: string | null;
  profile_deep_link?: string | null;
  is_verified?: boolean | null;
  follower_count?: number | null;
  following_count?: number | null;
  likes_count?: number | null;
  video_count?: number | null;
  scopes: string[];
  status: string;
  access_token_expires_at: string;
  refresh_token_expires_at: string;
  last_token_refresh_at?: string | null;
  profile_synced_at?: string | null;
};

export type TikTokVideo = {
  id: number;
  account_id: number;
  video_id: string;
  create_time?: string | null;
  cover_image_url?: string | null;
  share_url?: string | null;
  video_description?: string | null;
  duration?: number | null;
  height?: number | null;
  width?: number | null;
  title?: string | null;
  embed_link?: string | null;
  like_count?: number | null;
  comment_count?: number | null;
  share_count?: number | null;
  view_count?: number | null;
  is_aigc?: boolean | null;
  synced_at: string;
};

export type TikTokVideoSyncResult = {
  synced_count: number;
  cursor?: number | null;
  has_more: boolean;
};

export type AccountAnalyticsPoint = {
  captured_at: string;
  follower_count?: number | null;
  following_count?: number | null;
  likes_count?: number | null;
  video_count?: number | null;
};

export type AnalyticsDelta = {
  followers?: number | null;
  following?: number | null;
  likes?: number | null;
  videos?: number | null;
};

export type VideoAnalyticsSummary = {
  video_id: string;
  title?: string | null;
  share_url?: string | null;
  cover_image_url?: string | null;
  view_count?: number | null;
  like_count?: number | null;
  comment_count?: number | null;
  share_count?: number | null;
  view_delta?: number | null;
  like_delta?: number | null;
  comment_delta?: number | null;
  share_delta?: number | null;
  first_captured_at: string;
  last_captured_at: string;
};

export type TikTokAnalyticsReport = {
  account_id: number;
  days: number;
  account_points: AccountAnalyticsPoint[];
  account_deltas: AnalyticsDelta;
  top_videos: VideoAnalyticsSummary[];
  account_snapshot_count: number;
  video_snapshot_count: number;
};

export type AuditEvent = {
  id: number;
  event_type: string;
  account_id?: number | null;
  actor: string;
  status: string;
  detail?: string | null;
  created_at: string;
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
  auditEvents: (limit = 50) => json<AuditEvent[]>(`/api/audit/events?limit=${limit}`),
  startTikTokOAuth: (scopes?: string[]) =>
    json<OAuthStart>("/api/tiktok/oauth/start", {
      method: "POST",
      body: JSON.stringify({ scopes: scopes ?? null }),
    }),
  refreshTikTokAccount: (id: number) =>
    json<TikTokAccount>(`/api/tiktok/accounts/${id}/refresh`, { method: "POST" }),
  syncTikTokProfile: (id: number) =>
    json<TikTokAccount>(`/api/tiktok/accounts/${id}/sync-profile`, { method: "POST" }),
  tiktokVideos: (id: number, limit = 100, offset = 0) =>
    json<TikTokVideo[]>(`/api/tiktok/accounts/${id}/videos?limit=${limit}&offset=${offset}`),
  tiktokAnalytics: (id: number, days: 7 | 30 | 90) =>
    json<TikTokAnalyticsReport>(`/api/tiktok/accounts/${id}/analytics?days=${days}`),
  syncTikTokVideos: (id: number, cursor?: number | null, maxCount = 20) =>
    json<TikTokVideoSyncResult>(`/api/tiktok/accounts/${id}/videos/sync`, {
      method: "POST",
      body: JSON.stringify({ cursor: cursor ?? null, max_count: maxCount }),
    }),
  refreshTikTokVideos: (id: number, videoIds: string[]) =>
    json<TikTokVideo[]>(`/api/tiktok/accounts/${id}/videos/refresh`, {
      method: "POST",
      body: JSON.stringify({ video_ids: videoIds }),
    }),
  disconnectTikTokAccount: (id: number) =>
    json<TikTokAccount>(`/api/tiktok/accounts/${id}/disconnect`, { method: "POST" }),
};
