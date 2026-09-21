import { ReactNode } from "react";

import AnalyticsPanel from "./AnalyticsPanel";
import DirectPostPanel from "./DirectPostPanel";
import DraftUploadPanel from "./DraftUploadPanel";
import SchedulerPanel from "./SchedulerPanel";
import AccountVideoWorkspace, { VideoView } from "./AccountVideoWorkspace";
import { TikTokAccount, TikTokConfigStatus } from "./api";
import { accountStatusVi, scopeLabelVi } from "./vi";

export type AccountSection =
  | "basic"
  | "extended"
  | "account-stats"
  | "video-list"
  | "video-detail"
  | "video-stats"
  | "video-embed"
  | "upload-video"
  | "direct-video"
  | "photo-post"
  | "caption"
  | "privacy"
  | "comment"
  | "duet"
  | "stitch"
  | "cover"
  | "ai-label"
  | "commercial"
  | "post-status";

type Props = {
  account: TikTokAccount;
  section: AccountSection;
  onSectionChange: (section: AccountSection) => void;
  config: TikTokConfigStatus | null;
  busy: boolean;
  onSyncProfile: (id: number) => Promise<void>;
  onRefreshToken: (id: number) => Promise<void>;
  onReconnect: () => void;
  onDisconnect: (id: number) => Promise<void>;
};

const groups: {
  label: string;
  items: { id: AccountSection; icon: string; label: string; scope?: string }[];
}[] = [
  {
    label: "Hồ sơ",
    items: [
      { id: "basic", icon: "👤", label: "Hồ sơ cơ bản", scope: "user.info.basic" },
      { id: "extended", icon: "👤", label: "Hồ sơ mở rộng", scope: "user.info.profile" },
      { id: "account-stats", icon: "📊", label: "Thống kê tài khoản", scope: "user.info.stats" },
    ],
  },
  {
    label: "Video & dữ liệu",
    items: [
      { id: "video-list", icon: "🎬", label: "Danh sách video", scope: "video.list" },
      { id: "video-detail", icon: "🔎", label: "Chi tiết video", scope: "video.list" },
      { id: "video-stats", icon: "📈", label: "Thống kê từng video", scope: "video.list" },
      { id: "video-embed", icon: "▶️", label: "Nhúng video" },
    ],
  },
  {
    label: "Tải lên & đăng bài",
    items: [
      { id: "upload-video", icon: "⬆️", label: "Tải video lên", scope: "video.upload" },
      { id: "direct-video", icon: "🚀", label: "Đăng video trực tiếp", scope: "video.publish" },
      { id: "photo-post", icon: "🖼️", label: "Đăng ảnh", scope: "video.publish" },
    ],
  },
  {
    label: "Thiết lập bài đăng",
    items: [
      { id: "caption", icon: "📝", label: "Chú thích" },
      { id: "privacy", icon: "🔒", label: "Quyền xem" },
      { id: "comment", icon: "💬", label: "Bình luận" },
      { id: "duet", icon: "👥", label: "Duet" },
      { id: "stitch", icon: "✂️", label: "Stitch" },
      { id: "cover", icon: "🖼️", label: "Ảnh bìa video" },
      { id: "ai-label", icon: "🤖", label: "Nhãn AI" },
      { id: "commercial", icon: "💰", label: "Khai báo thương mại" },
    ],
  },
  {
    label: "Trạng thái",
    items: [{ id: "post-status", icon: "📡", label: "Trạng thái đăng" }],
  },
];

export default function AccountWorkspace({
  account,
  section,
  onSectionChange,
  config,
  busy,
  onSyncProfile,
  onRefreshToken,
  onReconnect,
  onDisconnect,
}: Props) {
  return (
    <div className="account-workspace">
      <AccountHeader
        account={account}
        config={config}
        busy={busy}
        onSyncProfile={onSyncProfile}
        onRefreshToken={onRefreshToken}
        onReconnect={onReconnect}
        onDisconnect={onDisconnect}
      />

      <nav className="account-feature-nav">
        {groups.map((group) => (
          <div className="feature-nav-group" key={group.label}>
            <span>{group.label}</span>
            <div>
              {group.items.map((item) => {
                const granted = !item.scope || account.scopes.includes(item.scope);
                return (
                  <button
                    key={item.id}
                    className={section === item.id ? "active" : ""}
                    onClick={() => onSectionChange(item.id)}
                  >
                    <span>{item.icon}</span>
                    <strong>{item.label}</strong>
                    {item.scope && (
                      <small className={granted ? "scope-granted" : "scope-missing"}>
                        {granted ? "Đã cấp quyền" : "Chưa cấp quyền"}
                      </small>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="account-feature-content">
        {renderSection(section, account)}
      </div>
    </div>
  );
}

function renderSection(section: AccountSection, account: TikTokAccount): ReactNode {
  const single = [account];

  if (section === "basic") return <BasicProfile account={account} />;
  if (section === "extended") return <ExtendedProfile account={account} />;
  if (section === "account-stats") {
    return (
      <>
        <AccountStats account={account} />
        <AnalyticsPanel accounts={single} />
      </>
    );
  }

  const videoMap: Partial<Record<AccountSection, VideoView>> = {
    "video-list": "list",
    "video-detail": "detail",
    "video-stats": "stats",
    "video-embed": "embed",
  };
  const videoView = videoMap[section];
  if (videoView) return <AccountVideoWorkspace account={account} view={videoView} />;

  if (section === "upload-video") return <DraftUploadPanel accounts={single} />;

  if (
    [
      "direct-video",
      "photo-post",
      "caption",
      "privacy",
      "comment",
      "duet",
      "stitch",
      "cover",
      "ai-label",
      "commercial",
    ].includes(section)
  ) {
    return (
      <>
        <PostingSettingIntro section={section} />
        <DirectPostPanel accounts={single} initialMode={section === "photo-post" ? "PHOTO" : "VIDEO"} />
      </>
    );
  }

  if (section === "post-status") {
    return (
      <>
        <PostingStatusIntro />
        <DirectPostPanel accounts={single} />
        <SchedulerPanel accounts={single} />
      </>
    );
  }

  return null;
}

function AccountHeader({
  account,
  config,
  busy,
  onSyncProfile,
  onRefreshToken,
  onReconnect,
  onDisconnect,
}: {
  account: TikTokAccount;
  config: TikTokConfigStatus | null;
  busy: boolean;
  onSyncProfile: (id: number) => Promise<void>;
  onRefreshToken: (id: number) => Promise<void>;
  onReconnect: () => void;
  onDisconnect: (id: number) => Promise<void>;
}) {
  const missingScopes = (config?.scopes ?? []).filter(
    (scope) => !account.scopes.includes(scope),
  );

  return (
    <section className="account-workspace-header">
      <div className="workspace-account-identity">
        {account.avatar_url ? (
          <img src={account.avatar_url} alt="" />
        ) : (
          <div className="workspace-avatar-placeholder">TT</div>
        )}
        <div>
          <div className="workspace-account-title">
            <h2>{account.display_name || "Tài khoản TikTok"}</h2>
            {account.is_verified && <span className="verified-badge">✓ Đã xác minh</span>}
          </div>
          <span>
            {account.username ? "@" + account.username : "Tài khoản #" + account.id}
          </span>
          <div className="workspace-account-meta">
            <span className={"badge " + (account.status === "CONNECTED" ? "badge-ok" : "")}>
              {accountStatusVi(account.status)}
            </span>
            <span>{account.scopes.length} quyền đã cấp</span>
            {account.profile_synced_at && (
              <span>
                Đồng bộ {new Date(account.profile_synced_at).toLocaleString("vi-VN")}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="workspace-account-actions">
        {account.status !== "CONNECTED" && (
          <button disabled={busy} onClick={onReconnect}>
            Kết nối lại
          </button>
        )}
        <button className="ghost" disabled={busy} onClick={() => onSyncProfile(account.id)}>
          Đồng bộ dữ liệu
        </button>
        <button className="ghost" disabled={busy} onClick={() => onRefreshToken(account.id)}>
          Làm mới token
        </button>
        <button className="danger" disabled={busy} onClick={() => onDisconnect(account.id)}>
          Ngắt kết nối
        </button>
      </div>

      <div className="workspace-scope-strip">
        {account.scopes.map((scope) => (
          <span className="scope-chip granted" key={scope}>
            {scopeLabelVi(scope)} · <code>{scope}</code>
          </span>
        ))}
        {missingScopes.map((scope) => (
          <span className="scope-chip missing" key={scope}>
            Chưa cấp · <code>{scope}</code>
          </span>
        ))}
      </div>
    </section>
  );
}

function BasicProfile({ account }: { account: TikTokAccount }) {
  return (
    <FeatureShell
      eyebrow="USER INFO API · USER.INFO.BASIC"
      title="Hồ sơ cơ bản"
      description="Dữ liệu nhận từ quyền user.info.basic của tài khoản đang chọn."
    >
      <div className="profile-overview">
        {account.avatar_url ? (
          <img className="profile-large-avatar" src={account.avatar_url} alt="" />
        ) : (
          <div className="profile-large-avatar placeholder">TT</div>
        )}
        <div className="profile-field-grid">
          <ProfileField label="open_id" value={account.open_id} copy />
          <ProfileField label="Tên hiển thị" value={account.display_name} />
          <ProfileField
            label="URL ảnh đại diện"
            value={account.avatar_url}
            link
          />
          <ProfileField
            label="Đồng bộ gần nhất"
            value={
              account.profile_synced_at
                ? new Date(account.profile_synced_at).toLocaleString("vi-VN")
                : null
            }
          />
        </div>
      </div>
    </FeatureShell>
  );
}

function ExtendedProfile({ account }: { account: TikTokAccount }) {
  if (!account.scopes.includes("user.info.profile")) {
    return (
      <PermissionRequired
        scope="user.info.profile"
        text="Tài khoản chưa cấp quyền đọc tên người dùng, tiểu sử, liên kết hồ sơ và trạng thái xác minh."
      />
    );
  }

  return (
    <FeatureShell
      eyebrow="USER INFO API · USER.INFO.PROFILE"
      title="Hồ sơ mở rộng"
      description="Các trường hồ sơ mở rộng mà TikTok cho phép với quyền user.info.profile."
    >
      <div className="profile-field-grid">
        <ProfileField label="Tên người dùng" value={account.username ? "@" + account.username : null} />
        <ProfileField label="Tiểu sử" value={account.bio_description} />
        <ProfileField label="Link hồ sơ" value={account.profile_deep_link} link />
        <ProfileField
          label="Trạng thái xác minh"
          value={account.is_verified === true ? "Đã xác minh" : "Chưa xác minh"}
        />
      </div>
    </FeatureShell>
  );
}

function AccountStats({ account }: { account: TikTokAccount }) {
  if (!account.scopes.includes("user.info.stats")) {
    return (
      <PermissionRequired
        scope="user.info.stats"
        text="Tài khoản chưa cấp quyền đọc follower, following, tổng lượt thích và số video."
      />
    );
  }

  return (
    <FeatureShell
      eyebrow="USER INFO API · USER.INFO.STATS"
      title="Thống kê tài khoản"
      description="Số liệu tài khoản thật do TikTok trả về. Biểu đồ lịch sử nằm ngay bên dưới."
    >
      <div className="account-stat-grid">
        <StatCard label="Người theo dõi" value={account.follower_count} />
        <StatCard label="Đang theo dõi" value={account.following_count} />
        <StatCard label="Tổng lượt thích" value={account.likes_count} />
        <StatCard label="Số video" value={account.video_count} />
      </div>
    </FeatureShell>
  );
}

function PostingSettingIntro({ section }: { section: AccountSection }) {
  const map: Partial<
    Record<AccountSection, { title: string; description: string; api: string }>
  > = {
    "direct-video": {
      title: "Đăng video trực tiếp",
      description:
        "Đăng video lên tài khoản đang chọn bằng Direct Post. Creator Info được kiểm tra lại trước khi gửi.",
      api: "video.publish",
    },
    "photo-post": {
      title: "Đăng ảnh",
      description:
        "Đăng ảnh trực tiếp hoặc chuẩn bị luồng ảnh theo Content Posting API của tài khoản đang chọn.",
      api: "video.publish / video.upload",
    },
    caption: {
      title: "Chú thích",
      description:
        "Thiết lập title/caption, hashtag và mention cho bài đang chuẩn bị đăng.",
      api: "Content Posting API",
    },
    privacy: {
      title: "Quyền xem",
      description:
        "Chỉ hiển thị các lựa chọn quyền xem mà Creator Info hiện tại của TikTok trả về.",
      api: "Content Posting API",
    },
    comment: {
      title: "Bình luận",
      description:
        "Cho phép hoặc tắt bình luận cho chính bài đang chuẩn bị đăng.",
      api: "disable_comment",
    },
    duet: {
      title: "Duet",
      description:
        "Cho phép hoặc tắt Duet cho bài video đang chuẩn bị đăng nếu TikTok cho phép.",
      api: "disable_duet",
    },
    stitch: {
      title: "Stitch",
      description:
        "Cho phép hoặc tắt Stitch cho bài video đang chuẩn bị đăng nếu TikTok cho phép.",
      api: "disable_stitch",
    },
    cover: {
      title: "Ảnh bìa video",
      description:
        "Chọn timestamp của video dùng làm ảnh cover. Giá trị không được vượt quá thời lượng video.",
      api: "video_cover_timestamp_ms",
    },
    "ai-label": {
      title: "Nhãn AI",
      description:
        "Khai báo nội dung do AI tạo cho bài đang chuẩn bị đăng.",
      api: "is_aigc",
    },
    commercial: {
      title: "Khai báo thương mại",
      description:
        "Khai báo nội dung quảng bá thương hiệu của mình hoặc paid partnership.",
      api: "Content Posting API",
    },
  };

  const item = map[section];
  if (!item) return null;

  return (
    <section className="account-feature-card feature-context-card">
      <div>
        <span className="eyebrow">{item.api}</span>
        <h3>{item.title}</h3>
        <p>{item.description}</p>
      </div>
    </section>
  );
}

function PostingStatusIntro() {
  return (
    <section className="account-feature-card feature-context-card">
      <div>
        <span className="eyebrow">TRẠNG THÁI ĐĂNG + WEBHOOK</span>
        <h3>Trạng thái đăng</h3>
        <p>
          Theo dõi processing, publish thành công/thất bại, publish_id, public post ID
          và lịch đăng của tài khoản đang chọn.
        </p>
      </div>
    </section>
  );
}

function FeatureShell({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="account-feature-card">
      <div className="feature-card-head">
        <div>
          <span className="eyebrow">{eyebrow}</span>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function PermissionRequired({ scope, text }: { scope: string; text: string }) {
  return (
    <section className="account-feature-card permission-required">
      <div>
        <span className="eyebrow">CHƯA CẤP QUYỀN</span>
        <h3>Chưa có quyền {scope}</h3>
        <p>{text}</p>
        <p>
          Quyền này vẫn được giữ trên giao diện. Sau khi TikTok cấp scope và tài khoản
          reconnect, dữ liệu thật sẽ hiển thị tại đây.
        </p>
      </div>
      <code>{scope}</code>
    </section>
  );
}

function ProfileField({
  label,
  value,
  link = false,
  copy = false,
}: {
  label: string;
  value?: string | null;
  link?: boolean;
  copy?: boolean;
}) {
  const actual = value || "—";

  return (
    <div className="profile-field">
      <span>{label}</span>
      <div className="profile-field-value">
        {link && value ? (
          <a href={value} target="_blank" rel="noreferrer">{value}</a>
        ) : (
          <strong>{actual}</strong>
        )}
        {copy && value && (
          <button
            className="copy-mini"
            onClick={() => void navigator.clipboard.writeText(value)}
          >
            Sao chép
          </button>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value?: number | null }) {
  return (
    <article className="account-stat-card">
      <span>{label}</span>
      <strong>{typeof value === "number" ? value.toLocaleString("vi-VN") : "—"}</strong>
    </article>
  );
}
