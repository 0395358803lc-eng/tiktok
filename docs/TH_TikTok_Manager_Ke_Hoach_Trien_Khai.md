# TH TikTok Manager — Kế hoạch triển khai chuyên nghiệp

**Ngày lập:** 2026-09-21  
**Mục tiêu:** Xây dựng hệ thống quản lý nhiều tài khoản TikTok cá nhân bằng API chính thức, OAuth và token riêng cho từng tài khoản.  
**Nguyên tắc:** API-first, dữ liệu thật, không mock trong luồng production, không phụ thuộc browser automation cho chức năng TikTok đã có API chính thức.

## 1. Mục tiêu sản phẩm

Hệ thống cần cho phép một quản trị viên:
- Kết nối nhiều tài khoản TikTok thông qua OAuth.
- Quản lý trạng thái kết nối và vòng đời token của từng tài khoản.
- Đồng bộ profile, số liệu tài khoản và video.
- Quản lý thư viện nội dung dùng để đăng.
- Tạo campaign, lịch đăng và job riêng cho từng tài khoản.
- Theo dõi trạng thái publish, lỗi, retry và lịch sử thao tác.
- Tổng hợp analytics nhiều tài khoản trên một dashboard.
- Vận hành ổn định khi số lượng tài khoản tăng lên hàng chục hoặc hàng trăm.

## 2. Phạm vi phiên bản 1.0

V1.0 gồm Admin Authentication, TikTok OAuth, Token Vault, Account Manager, Profile/Video Sync, Analytics, Content Library, Campaign, Job Queue, Scheduler, Publishing, Logs, Error Center và Monitoring.

## 3. Kiến trúc tổng thể

```text
Admin Frontend
      |
      v
Backend API
      |
      +--> PostgreSQL
      +--> Redis
      +--> Background Worker
      +--> Scheduler
      +--> Media Storage
      +--> TikTok Open API
```

### Stack đề xuất
- Frontend: React + TypeScript.
- Backend: FastAPI + Python.
- Database: PostgreSQL.
- Queue/Cache: Redis.
- Worker: Celery hoặc RQ.
- Scheduler: Celery Beat hoặc service riêng.
- Media storage: S3-compatible object storage.
- Deployment: Docker.
- Reverse proxy: Nginx hoặc Cloudflare.
- Monitoring: health checks + structured logs.

### Quy tắc kiến trúc
- TikTok integration phải tách thành service riêng.
- Không lưu TikTok token trong localStorage.
- Không để client secret trong frontend.
- Mỗi account có token, job, quota, lỗi và trạng thái độc lập.

## 4. Batch A — Foundation

### Công việc
- A01: Chuẩn hóa cấu trúc project.
- A02: Cấu hình PostgreSQL và migration framework.
- A03: Cấu hình Redis.
- A04: Xây admin authentication.
- A05: Xây config/env validation.
- A06: Tạo structured logging.
- A07: Tạo endpoint /health và /ready.
- A08: Docker hóa môi trường local/production.
- A09: Thiết lập test framework và CI cơ bản.

### Điều kiện nghiệm thu
- Frontend/backend chạy được từ tài liệu hướng dẫn.
- Database migration PASS.
- Redis reachable.
- Admin login hoạt động.
- /health và /ready trả đúng trạng thái.
- Không có secret thật trong repository.
- Không dùng mock TikTok data như dữ liệu production.

## 5. Batch B — TikTok OAuth & Token Manager
- B01: Tích hợp TikTok Login Kit/OAuth.
- B02: Nút Connect TikTok Account.
- B03: Tạo và kiểm tra OAuth state.
- B04: Nhận authorization code.
- B05: Backend đổi code lấy token.
- B06: Lưu open_id, scopes và expiry.
- B07: Mã hóa access/refresh token trước khi lưu DB.
- B08: Auto refresh token.
- B09: Reconnect flow khi token bị revoke hoặc hết hạn.

## 6. Batch C — Account Manager & Profile Sync

- C01: Danh sách tài khoản đã kết nối.
- C02: Tìm kiếm và lọc theo username/trạng thái.
- C03: Trang chi tiết từng tài khoản.
- C04: Đồng bộ hồ sơ thật từ TikTok API.
- C05: Đồng bộ số liệu mà API và quyền đã cấp cho phép.
- C06: Lưu snapshot thống kê theo thời gian.
- C07: Manual sync có kiểm soát tần suất gọi API.
- C08: Nếu thiếu quyền, hiển thị lỗi rõ ràng và không sinh dữ liệu giả.

### Điều kiện nghiệm thu Batch C
- Dữ liệu test phải lấy từ API thật.
- Reload trang không làm mất account đã kết nối.
- Database là nguồn dữ liệu chính.
- Lỗi API của một account không làm hỏng toàn bộ dashboard.

## 7. Batch D — Video Manager & Analytics

- D01: Đồng bộ danh sách video theo từng tài khoản.
- D02: Hỗ trợ phân trang/cursor.
- D03: Đồng bộ metadata video.
- D04: Đồng bộ view/like/comment/share khi API cho phép.
- D05: Lưu metric snapshot theo thời gian.
- D06: Dashboard Today / 7 days / 30 days / Custom.
- D07: Top accounts và top videos.
- D08: Biểu đồ tăng trưởng dựa trên snapshot thật.

### Điều kiện nghiệm thu Batch D
- Video hiển thị đúng theo từng account.
- Analytics chỉ tính từ dữ liệu DB/API thật.
- Khi API lỗi không sinh số liệu giả.
- Khi thiếu quyền phải báo đúng nguyên nhân.

## 8. Batch E — Content Library & Campaign

- E01: Upload video/ảnh vào media storage.
- E02: Quản lý metadata nội dung.
- E03: Caption/hashtag editor.
- E04: Campaign CRUD.
- E05: Chọn các tài khoản đã được chủ sở hữu cấp quyền.
- E06: Lập lịch nội dung theo từng tài khoản.
- E07: Validate media trước khi tạo tác vụ.

## 9. Batch F — Queue, Scheduler & Publishing

- F01: Tạo bảng tác vụ đăng nội dung.
- F02: Mỗi tài khoản có tác vụ độc lập.
- F03: Queue bằng Redis.
- F04: Worker nhận và xử lý tác vụ.
- F05: Scheduler chỉ enqueue, không thực thi trực tiếp trong HTTP request.
- F06: Tích hợp TikTok Content Posting API chính thức.
- F07: Theo dõi trạng thái xử lý.
- F08: Retry có giới hạn với lỗi tạm thời.
- F09: Exponential backoff khi phù hợp.
- F10: Rate-limit manager.
- F11: Quota manager dựa trên giới hạn API hiện hành.
- F12: Idempotency để tránh đăng trùng do retry/restart.

### Trạng thái tác vụ
QUEUED -> SCHEDULED -> PROCESSING -> UPLOADING -> PUBLISHING -> SUCCESS
Nhánh khác: RETRY, FAILED, CANCELLED.

### Quy tắc tuân thủ
- Chỉ sử dụng tài khoản đã tự cấp quyền OAuth.
- Chỉ gọi các hành động TikTok API chính thức hỗ trợ.
- Không tự động follow, like, comment hoặc DM nếu Open API không cung cấp quyền tương ứng.
- Không dùng hệ thống để tạo tương tác giả hoặc spam.
- Giới hạn API phải được đọc từ tài liệu TikTok mới nhất trước mỗi release.

## 10. Batch G — Security, Monitoring & Production Hardening

### Security checklist
- Thông tin bí mật chỉ tồn tại phía server.
- Mã truy cập được mã hóa khi lưu trữ.
- HTTPS only.
- Kiểm tra OAuth state/CSRF.
- Secure admin session.
- Secret redaction trong log.
- Rate limiting cho API nội bộ.
- Database backup và restore test.
- Audit log cho thao tác quản trị.
- Không lưu mật khẩu TikTok.

### Monitoring bắt buộc
Theo dõi:
- API server.
- PostgreSQL.
- Redis.
- Worker.
- Scheduler.
- Media storage.
- TikTok API connectivity.
- Queue depth.
- Failed jobs.
- Accounts cần kết nối lại.

### Error Center
Mỗi lỗi cần có account_id, job_id nếu có, error code, message đã sanitize, timestamp, retryable và suggested action.

## 11. Test & Acceptance Suite

Phải có:
- Unit tests.
- Integration tests.
- OAuth tests.
- Quyền truy cập/renewal tests.
- API contract tests.
- Rate-limit tests.
- Scheduler tests.
- Queue tests.
- Publishing tests.
- Database migration tests.
- Frontend tests.
- End-to-end tests.

### Các case bắt buộc
- Quyền truy cập hết hạn hoặc bị thu hồi.
- Thiếu scope.
- HTTP 401/403/429/5xx.
- Upload thất bại.
- Processing kéo dài.
- Worker restart giữa tác vụ.
- Redis restart.
- Backend restart.
- Duplicate job.
- Database mất kết nối tạm thời.

Mọi case phải có log, trạng thái cuối rõ ràng và không làm mất tính nhất quán dữ liệu.

## 12. Tiêu chuẩn Release 1.0

Chỉ release khi:
- Frontend build PASS.
- Backend tests PASS.
- Database migration PASS.
- OAuth PASS với tài khoản thật.
- Gia hạn quyền truy cập PASS.
- Multi-account PASS.
- Profile API PASS.
- Video API PASS.
- Scheduler PASS.
- Queue PASS.
- Rate-limit handling PASS.
- Security scan PASS.
- E2E PASS.
- Không mock TikTok data trong production flow.
- Không thông tin bí mật trong frontend hoặc repository.
- API documentation và deployment documentation hoàn chỉnh.

## 13. Thứ tự triển khai bắt buộc
1. Batch A — Foundation.
2. Batch B — OAuth & Access Management.
3. Batch C — Account Manager.
4. Batch D — Video & Analytics.
5. Nghiệm thu trung gian bằng API thật.
6. Batch E — Content Library & Campaign.
7. Batch F — Queue / Scheduler / Publishing.
8. Batch G — Production Hardening.
9. Nghiệm thu cuối.
10. Release 1.0.

Không được nhảy thẳng sang publishing trước khi OAuth, lifecycle quyền truy cập, account sync và observability đã PASS.

## 14. Nguyên tắc dành cho đội kỹ thuật

- API-first và ưu tiên API chính thức TikTok.
- Server-backed state; database là nguồn sự thật.
- Một account = một identity/lifecycle riêng.
- Một publishing request = một traceable job riêng.
- Phân biệt tuyệt đối dữ liệu thật và fixture/test data.
- Không che lỗi TikTok bằng dữ liệu giả.
- Không ghi secret vào logs.
- Mọi background task phải idempotent và có retry policy rõ ràng.
- Mọi thay đổi schema phải đi qua migration.
- Mọi endpoint mới phải có test và API documentation.
- Không mở rộng sang hành vi mà TikTok Open API không cấp phép.

## 15. Tài liệu phải đối chiếu trước mỗi release

Đội kỹ thuật cần kiểm tra bản mới nhất của:
- TikTok Login Kit / OAuth documentation.
- TikTok API Scopes.
- User Info API.
- Video List / Video Query API.
- Content Posting API.
- TikTok rate limits.
- Content Sharing Guidelines.

## 16. Kết luận triển khai

Ưu tiên hoàn thành và nghiệm thu Batch A → D trước. Chỉ sau khi đa tài khoản OAuth, cơ chế duy trì quyền truy cập, profile/video sync và analytics đều chạy bằng API thật mới triển khai Batch E → G.

Báo cáo này là specification gốc để giao cho nhân viên kỹ thuật; mọi thay đổi phạm vi phải được ghi lại trong changelog và nghiệm thu lại các hạng mục liên quan.


## 17. Implementation Override — Native Server Runtime

**Effective 2026-09-21:** Docker is removed from the implementation scope by project decision.

The deployment/runtime model is now:
- Direct native/user-space processes on the server.
- PostgreSQL runs from the project-local Conda runtime.
- Redis protocol cache is provided by project-local Valkey.
- FastAPI runs with the project Python virtual environment.
- Frontend runs from the local Node.js installation.
- Service control uses `scripts/start-native.sh`, `status-native.sh`, and `stop-native.sh`.

Any earlier Docker references in this planning document are superseded by this section.
