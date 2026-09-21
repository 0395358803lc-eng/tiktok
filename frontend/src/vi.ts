export function accountStatusVi(status: string) {
  const map: Record<string, string> = {
    CONNECTED: "Đã kết nối",
    REAUTH_REQUIRED: "Cần cấp quyền lại",
    ERROR: "Lỗi",
    REVOKED: "Đã thu hồi quyền",
  };
  return map[status] ?? status;
}

export function jobStatusVi(status: string) {
  const map: Record<string, string> = {
    QUEUED: "Đang chờ",
    INITIALIZING: "Đang khởi tạo",
    UPLOADING: "Đang tải lên",
    SUBMITTED: "Đã gửi",
    PROCESSING_UPLOAD: "Đang xử lý upload",
    PROCESSING_DOWNLOAD: "Đang tải dữ liệu",
    SEND_TO_USER_INBOX: "Đã gửi tới Hộp thư TikTok",
    PUBLISH_COMPLETE: "Đăng thành công",
    FAILED: "Thất bại",
    CANCELED: "Đã hủy",
    SCHEDULED: "Đã lên lịch",
    READY: "Sẵn sàng",
    RUNNING: "Đang chạy",
    COMPLETED: "Hoàn tất",
  };
  return map[status] ?? status;
}

export function auditStatusVi(status: string) {
  const map: Record<string, string> = {
    SUCCESS: "Thành công",
    WARNING: "Cảnh báo",
    ERROR: "Lỗi",
  };
  return map[status] ?? status;
}

export function scopeLabelVi(scope: string) {
  const map: Record<string, string> = {
    "user.info.basic": "Hồ sơ cơ bản",
    "user.info.profile": "Hồ sơ mở rộng",
    "user.info.stats": "Thống kê tài khoản",
    "video.list": "Danh sách video",
    "video.upload": "Upload bản nháp",
    "video.publish": "Đăng trực tiếp",
  };
  return map[scope] ?? scope;
}
