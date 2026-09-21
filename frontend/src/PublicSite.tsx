const EFFECTIVE_DATE = "21 tháng 9, 2026";

function SiteHeader() {
  return (
    <header className="public-header">
      <a className="public-brand" href="/">
        <span className="mark">TH</span>
        <span>
          <strong>TH TikTok Manager</strong>
          <small>Quản lý tài khoản được ủy quyền</small>
        </span>
      </a>
      <nav className="public-nav" aria-label="Điều hướng chính">
        <a href="/#features">Tính năng</a>
        <a href="/#security">Bảo mật</a>
        <a href="/terms">Điều khoản</a>
        <a href="/privacy">Quyền riêng tư</a>
        <a className="nav-cta" href="/admin">Quản trị</a>
      </nav>
    </header>
  );
}

function SiteFooter() {
  return (
    <footer className="public-footer">
      <div>
        <strong>TH TikTok Manager</strong>
        <span>Kết nối tài khoản sử dụng luồng OAuth chính thức của TikTok.</span>
      </div>
      <div className="footer-links">
        <a href="/terms">Điều khoản dịch vụ</a>
        <a href="/privacy">Chính sách quyền riêng tư</a>
        <a href="/admin">Truy cập quản trị</a>
      </div>
    </footer>
  );
}

export function PublicHome() {
  return (
    <main className="public-shell">
      <SiteHeader />

      <section className="public-hero">
        <div>
          <span className="eyebrow">QUẢN LÝ TÀI KHOẢN ĐƯỢC ỦY QUYỀN</span>
          <h1>Kết nối và quản lý tài khoản TikTok qua OAuth chính thức.</h1>
          <p>
            TH TikTok Manager giúp người dùng được ủy quyền kết nối tài khoản, đồng bộ
            dữ liệu được phép, quản lý video và các luồng đăng nội dung từ một giao diện
            quản trị tập trung.
          </p>
          <div className="hero-actions">
            <a className="button-link" href="/admin">Mở trang quản trị</a>
            <a className="text-link" href="/privacy">Cách dữ liệu được xử lý</a>
          </div>
        </div>

        <div className="public-card">
          <span className="eyebrow">TÍCH HỢP HIỆN TẠI</span>
          <h2>Ủy quyền tài khoản chính thức</h2>
          <p>
            Người dùng cấp quyền trực tiếp trên TikTok. Dịch vụ không yêu cầu hoặc thu thập
            mật khẩu TikTok. Mỗi tính năng chỉ hoạt động khi ứng dụng được TikTok cho phép
            sản phẩm/scope tương ứng và người dùng đã cấp quyền đó.
          </p>
          <div className="public-facts">
            <span>Ủy quyền OAuth 2.0</span>
            <span>Hồ sơ và phân tích</span>
            <span>Thư viện video và đăng nội dung</span>
            <span>Token lưu phía máy chủ</span>
          </div>
        </div>
      </section>

      <section className="public-section" id="features">
        <span className="eyebrow">TÍNH NĂNG</span>
        <h2>Xây dựng trên cơ chế cấp quyền rõ ràng của người dùng.</h2>
        <div className="feature-grid">
          <article>
            <h3>Kết nối tài khoản</h3>
            <p>Kết nối từng tài khoản riêng biệt qua TikTok Login Kit và sự đồng ý rõ ràng.</p>
          </article>
          <article>
            <h3>Hồ sơ và thống kê</h3>
            <p>Đồng bộ các trường hồ sơ và chỉ số tài khoản khi scope tương ứng đã được cấp.</p>
          </article>
          <article>
            <h3>Thư viện video và phân tích</h3>
            <p>
              Lấy video công khai của tài khoản được ủy quyền, làm mới chỉ số và xây dựng
              snapshot hiệu suất theo thời gian khi quyền video đã được cấp.
            </p>
          </article>
          <article>
            <h3>Tải bản nháp</h3>
            <p>
              Gửi video hoặc ảnh được người dùng cho phép tới Hộp thư TikTok dưới dạng bản
              nháp để nhà sáng tạo hoàn thiện việc chỉnh sửa và đăng.
            </p>
          </article>
          <article>
            <h3>Đăng trực tiếp và lên lịch</h3>
            <p>
              Chuẩn bị metadata Direct Post, tuân theo Creator Info hiện tại và vận hành
              hàng đợi đăng bài theo Content Posting API.
            </p>
          </article>
          <article>
            <h3>Vận hành và nhật ký</h3>
            <p>
              Theo dõi token, scope, webhook, trạng thái đăng bài, backup và sự kiện tài khoản
              từ một trung tâm điều hành.
            </p>
          </article>
        </div>
      </section>

      <section className="public-section split-section" id="security">
        <div>
          <span className="eyebrow">BẢO MẬT</span>
          <h2>Thông tin nhạy cảm được giữ phía máy chủ.</h2>
        </div>
        <div>
          <p>
            Access token và refresh token được lưu phía máy chủ ở dạng mã hóa. Authorization
            code và OAuth state không được chủ động ghi vào access log của ứng dụng.
            Phiên quản trị được lưu phía máy chủ và dùng cookie HttpOnly.
          </p>
          <p>
            Người dùng có thể ngắt kết nối để thu hồi quyền TikTok. Ứng dụng chỉ yêu cầu
            các quyền cần cho những tính năng đã triển khai.
          </p>
        </div>
      </section>

      <section className="public-section legal-callout">
        <div>
          <span className="eyebrow">MINH BẠCH</span>
          <h2>Đọc chính sách trước khi kết nối tài khoản.</h2>
        </div>
        <div className="hero-actions">
          <a className="button-link" href="/privacy">Chính sách quyền riêng tư</a>
          <a className="button-link secondary" href="/terms">Điều khoản dịch vụ</a>
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}

export function TermsPage() {
  return (
    <main className="public-shell legal-page">
      <SiteHeader />
      <article className="legal-document">
        <span className="eyebrow">PHÁP LÝ</span>
        <h1>Điều khoản dịch vụ</h1>
        <p className="legal-date">Ngày hiệu lực: {EFFECTIVE_DATE}</p>

        <h2>1. Dịch vụ</h2>
        <p>
          TH TikTok Manager cung cấp công cụ để người dùng kết nối các tài khoản TikTok mà
          họ được phép quản lý, đồng bộ dữ liệu hồ sơ và phân tích được cấp quyền, quản lý
          thông tin video công khai, chuẩn bị bản nháp, Direct Post, lịch đăng, duy trì kết
          nối OAuth và thu hồi kết nối. Mỗi tính năng phụ thuộc vào sản phẩm và scope TikTok
          đã cấp cho ứng dụng và được người dùng cho phép.
        </p>

        <h2>2. Sử dụng được ủy quyền</h2>
        <p>
          Bạn chỉ được sử dụng dịch vụ với tài khoản và dữ liệu mà bạn có quyền truy cập.
          Không được dùng dịch vụ để mạo danh người khác, vi phạm pháp luật, vượt qua cơ chế
          kiểm soát của nền tảng hoặc gây can thiệp tới TikTok hay hệ thống khác.
        </p>

        <h2>3. Cấp quyền tài khoản</h2>
        <p>
          Quyền truy cập tài khoản TikTok được cấp thông qua luồng OAuth của TikTok.
          Dịch vụ không yêu cầu mật khẩu TikTok. Người dùng chịu trách nhiệm xem lại các
          quyền TikTok hiển thị trước khi xác nhận cấp quyền.
        </p>

        <h2>4. Khả dụng</h2>
        <p>
          Tính năng có thể thay đổi hoặc tạm ngừng khi TikTok thay đổi API, scope, trạng thái
          review, rate limit hoặc yêu cầu nền tảng. Dịch vụ cũng có thể gián đoạn để bảo trì
          hoặc xử lý vấn đề bảo mật.
        </p>

        <h2>5. Trách nhiệm bảo mật</h2>
        <p>
          Người dùng có trách nhiệm bảo vệ thông tin đăng nhập quản trị và thiết bị của mình.
          Khi nghi ngờ truy cập trái phép, cần xử lý kịp thời và ngắt kết nối integration liên
          quan khi phù hợp.
        </p>

        <h2>6. Ngắt kết nối</h2>
        <p>
          Người dùng có thể ngắt kết nối tài khoản TikTok khỏi trang quản trị. Quyền truy cập
          cũng có thể dừng khi authorization hết hạn, bị thu hồi hoặc không còn đáp ứng yêu
          cầu của TikTok.
        </p>

        <h2>7. Quyền riêng tư</h2>
        <p>
          Việc thu thập và sử dụng thông tin được mô tả tại
          <a href="/privacy"> Chính sách quyền riêng tư</a>.
        </p>

        <h2>8. Thay đổi</h2>
        <p>
          Điều khoản có thể được cập nhật khi chức năng dịch vụ hoặc yêu cầu của nền tảng thay
          đổi. Ngày hiệu lực phía trên xác định phiên bản hiện tại.
        </p>
      </article>
      <SiteFooter />
    </main>
  );
}

export function PrivacyPage() {
  return (
    <main className="public-shell legal-page">
      <SiteHeader />
      <article className="legal-document">
        <span className="eyebrow">PHÁP LÝ</span>
        <h1>Chính sách quyền riêng tư</h1>
        <p className="legal-date">Ngày hiệu lực: {EFFECTIVE_DATE}</p>

        <h2>1. Thông tin được xử lý</h2>
        <p>
          Khi người dùng cấp quyền TikTok, dịch vụ có thể xử lý định danh tài khoản, tên hiển
          thị, avatar, trường hồ sơ mở rộng, thống kê tài khoản, metadata/chỉ số video công
          khai, scope đã cấp, access token, refresh token, thời hạn token, trạng thái kết nối
          và thời điểm đồng bộ khi quyền tương ứng đã được cấp. Với luồng nội dung, dịch vụ
          cũng có thể xử lý metadata media, URL ảnh do người dùng cung cấp, caption, lựa chọn
          quyền xem/tương tác, trạng thái draft/direct-post, lịch đăng, publish ID, public post
          ID và sự kiện webhook. Hoạt động đăng nhập quản trị và thao tác tài khoản được ghi
          lại phục vụ bảo mật và vận hành.
        </p>

        <h2>2. Cách lấy thông tin</h2>
        <p>
          Dữ liệu tài khoản TikTok được lấy qua OAuth và API chính thức sau khi người dùng cấp
          quyền. Dịch vụ không thu thập mật khẩu TikTok của người dùng.
        </p>

        <h2>3. Mục đích sử dụng</h2>
        <p>
          Thông tin được dùng để duy trì kết nối được ủy quyền, hiển thị hồ sơ/thống kê được
          phép, đồng bộ video công khai, xây dựng phân tích lịch sử, thực hiện luồng bản nháp
          hoặc Direct Post do người dùng yêu cầu, vận hành lịch đăng, xử lý webhook TikTok,
          làm mới quyền truy cập, hỗ trợ ngắt kết nối/thu hồi, chẩn đoán hệ thống và duy trì
          nhật ký bảo mật.
        </p>

        <h2>4. Lưu trữ và bảo mật</h2>
        <p>
          Access token và refresh token được lưu phía máy chủ ở dạng mã hóa. Media cục bộ đã
          staging được lưu phía máy chủ cho luồng nội dung tương ứng và không được công khai
          trên website. Authorization code, OAuth state, raw token và mật khẩu quản trị không
          được chủ động hiển thị trong UI hoặc ghi vào access log. Phiên quản trị dùng dữ liệu
          phiên phía máy chủ và cookie HttpOnly.
        </p>

        <h2>5. Chia sẻ dữ liệu</h2>
        <p>
          Dịch vụ chỉ gửi thông tin tới TikTok khi cần để thực hiện thao tác API mà người dùng
          đã yêu cầu và cấp quyền. Dịch vụ không chủ động bán OAuth token hoặc dữ liệu hồ sơ
          của tài khoản đã kết nối.
        </p>

        <h2>6. Thời gian lưu giữ</h2>
        <p>
          Dữ liệu kết nối, đồng bộ, đăng bài, webhook và analytics được giữ trong thời gian cần
          thiết để vận hành integration và duy trì lịch sử bảo mật. Media staging có thể được
          giữ khi cần cho draft/publishing và phục hồi vận hành. OAuth state hết hạn được tự
          động dọn dẹp. Backup và audit có thể được giữ trong thời hạn phù hợp cho bảo mật và
          phục hồi.
        </p>

        <h2>7. Quyền kiểm soát của người dùng</h2>
        <p>
          Tài khoản đã kết nối có thể được ngắt khỏi trang quản trị, đồng thời ứng dụng yêu cầu
          thu hồi authorization TikTok hiện tại. Người dùng cũng có thể quản lý quyền trực tiếp
          trên TikTok khi nền tảng cung cấp cơ chế tương ứng.
        </p>

        <h2>8. Thay đổi</h2>
        <p>
          Chính sách có thể được cập nhật khi chức năng dịch vụ hoặc yêu cầu nền tảng thay đổi.
          Ngày hiệu lực phía trên xác định phiên bản hiện tại.
        </p>
      </article>
      <SiteFooter />
    </main>
  );
}
