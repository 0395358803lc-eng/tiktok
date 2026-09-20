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

export type MediaAsset = {
  id: number;
  kind: string;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  duration_seconds?: number | null;
  created_at: string;
};

export type DraftJob = {
  id: number;
  account_id: number;
  media_asset_id?: number | null;
  media_type: string;
  source_type: string;
  title?: string | null;
  description?: string | null;
  publish_id?: string | null;
  status: string;
  fail_reason?: string | null;
  uploaded_bytes?: number | null;
  downloaded_bytes?: number | null;
  public_post_ids: string[];
  created_at: string;
  updated_at: string;
};

export type CreatorInfo = {
  creator_avatar_url?: string | null;
  creator_username?: string | null;
  creator_nickname?: string | null;
  privacy_level_options: string[];
  comment_disabled: boolean;
  duet_disabled: boolean;
  stitch_disabled: boolean;
  max_video_post_duration_sec?: number | null;
};

export type PublishJob = {
  id: number;
  account_id: number;
  media_asset_id?: number | null;
  media_type: string;
  source_type: string;
  title?: string | null;
  description?: string | null;
  privacy_level: string;
  disable_comment: boolean;
  disable_duet: boolean;
  disable_stitch: boolean;
  auto_add_music: boolean;
  brand_content_toggle: boolean;
  brand_organic_toggle: boolean;
  is_aigc: boolean;
  video_cover_timestamp_ms?: number | null;
  publish_id?: string | null;
  status: string;
  fail_reason?: string | null;
  uploaded_bytes?: number | null;
  downloaded_bytes?: number | null;
  public_post_ids: string[];
  scheduled_at?: string | null;
  schedule_status: string;
  retry_count: number;
  max_retries: number;
  next_attempt_at?: string | null;
  last_attempt_at?: string | null;
  canceled_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type PublishSchedule = {
  days: number;
  total: number;
  scheduled: number;
  ready: number;
  running: number;
  completed: number;
  failed: number;
  canceled: number;
  jobs: PublishJob[];
};

export type WebhookEvent = {
  id: number;
  event_type: string;
  user_open_id?: string | null;
  event_created_at?: string | null;
  status: string;
  attempts: number;
  error_detail?: string | null;
  received_at: string;
  processed_at?: string | null;
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

async function multipart<T>(url: string, data: FormData): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    credentials: "include",
    body: data,
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
  mediaAssets: () => json<MediaAsset[]>("/api/tiktok/media"),
  uploadVideoMedia: (file: File, durationSeconds?: number) => {
    const data = new FormData();
    data.append("file", file);
    if (typeof durationSeconds === "number") {
      data.append("duration_seconds", String(durationSeconds));
    }
    return multipart<MediaAsset>("/api/tiktok/media/video", data);
  },
  creatorInfo: (accountId: number) =>
    json<CreatorInfo>("/api/tiktok/accounts/" + accountId + "/creator-info", {
      method: "POST",
    }),
  publishJobs: (accountId?: number) =>
    json<PublishJob[]>(
      "/api/tiktok/publish-jobs" + (accountId ? "?account_id=" + accountId : "")
    ),
  createVideoPublish: (
    accountId: number,
    input: {
      media_asset_id: number;
      privacy_level: string;
      title?: string;
      allow_comment: boolean;
      allow_duet: boolean;
      allow_stitch: boolean;
      brand_content_toggle: boolean;
      brand_organic_toggle: boolean;
      is_aigc: boolean;
      video_cover_timestamp_ms?: number;
      consent_music_usage: boolean;
      consent_branded_policy: boolean;
      scheduled_at?: string;
      max_retries?: number;
    },
  ) =>
    json<PublishJob>("/api/tiktok/accounts/" + accountId + "/publish/video", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  createPhotoPublish: (
    accountId: number,
    input: {
      photo_urls: string[];
      cover_index: number;
      title?: string;
      description?: string;
      privacy_level: string;
      allow_comment: boolean;
      auto_add_music: boolean;
      brand_content_toggle: boolean;
      brand_organic_toggle: boolean;
      is_aigc: boolean;
      consent_music_usage: boolean;
      consent_branded_policy: boolean;
      scheduled_at?: string;
      max_retries?: number;
    },
  ) =>
    json<PublishJob>("/api/tiktok/accounts/" + accountId + "/publish/photo", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  refreshPublishJob: (jobId: number) =>
    json<PublishJob>("/api/tiktok/publish-jobs/" + jobId + "/refresh", {
      method: "POST",
    }),
  publishSchedule: (days: 7 | 30, accountId?: number) => {
    const query = new URLSearchParams({ days: String(days) });
    if (accountId) query.set("account_id", String(accountId));
    return json<PublishSchedule>("/api/tiktok/publish-schedule?" + query.toString());
  },
  cancelPublishJob: (jobId: number) =>
    json<PublishJob>("/api/tiktok/publish-jobs/" + jobId + "/cancel", { method: "POST" }),
  reschedulePublishJob: (jobId: number, scheduledAt: string) =>
    json<PublishJob>("/api/tiktok/publish-jobs/" + jobId + "/reschedule", {
      method: "POST",
      body: JSON.stringify({ scheduled_at: scheduledAt }),
    }),
  retryPublishJob: (jobId: number) =>
    json<PublishJob>("/api/tiktok/publish-jobs/" + jobId + "/retry", { method: "POST" }),
  draftJobs: (accountId?: number) =>
    json<DraftJob[]>(`/api/tiktok/drafts${accountId ? `?account_id=${accountId}` : ""}`),
  createVideoDraft: (accountId: number, mediaAssetId: number) =>
    json<DraftJob>(`/api/tiktok/accounts/${accountId}/drafts/video`, {
      method: "POST",
      body: JSON.stringify({ media_asset_id: mediaAssetId }),
    }),
  createPhotoDraft: (
    accountId: number,
    input: {
      photo_urls: string[];
      cover_index: number;
      title?: string;
      description?: string;
      is_aigc: boolean;
    },
  ) =>
    json<DraftJob>(`/api/tiktok/accounts/${accountId}/drafts/photo`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  refreshDraft: (jobId: number) =>
    json<DraftJob>(`/api/tiktok/drafts/${jobId}/refresh`, { method: "POST" }),
  auditEvents: (limit = 50) => json<AuditEvent[]>(`/api/audit/events?limit=${limit}`),
  webhookEvents: (limit = 100) =>
    json<WebhookEvent[]>(`/api/tiktok/webhook-events?limit=${limit}`),
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
