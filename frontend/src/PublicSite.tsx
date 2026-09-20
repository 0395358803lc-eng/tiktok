const EFFECTIVE_DATE = "September 21, 2026";

function SiteHeader() {
  return (
    <header className="public-header">
      <a className="public-brand" href="/">
        <span className="mark">TH</span>
        <span>
          <strong>TH TikTok Manager</strong>
          <small>Authorized account management</small>
        </span>
      </a>
      <nav className="public-nav" aria-label="Primary navigation">
        <a href="/#features">Features</a>
        <a href="/#security">Security</a>
        <a href="/terms">Terms</a>
        <a href="/privacy">Privacy</a>
        <a className="nav-cta" href="/admin">Admin</a>
      </nav>
    </header>
  );
}

function SiteFooter() {
  return (
    <footer className="public-footer">
      <div>
        <strong>TH TikTok Manager</strong>
        <span>Account connections use TikTok's official OAuth authorization flow.</span>
      </div>
      <div className="footer-links">
        <a href="/terms">Terms of Service</a>
        <a href="/privacy">Privacy Policy</a>
        <a href="/admin">Admin access</a>
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
          <span className="eyebrow">AUTHORIZED ACCOUNT MANAGEMENT</span>
          <h1>Connect and manage TikTok accounts through official OAuth.</h1>
          <p>
            TH TikTok Manager helps authorized users connect their TikTok accounts,
            view basic profile information, monitor connection status, refresh access,
            and revoke authorization from one secure control plane.
          </p>
          <div className="hero-actions">
            <a className="button-link" href="/admin">Open admin</a>
            <a className="text-link" href="/privacy">How data is handled</a>
          </div>
        </div>
        <div className="public-card">
          <span className="eyebrow">CURRENT INTEGRATION</span>
          <h2>Login Kit</h2>
          <p>
            Users authorize access on TikTok. The service does not request or collect
            TikTok passwords. The current permission is limited to basic profile access.
          </p>
          <div className="public-facts">
            <span>OAuth 2.0 authorization</span>
            <span>Basic profile data</span>
            <span>Server-side token storage</span>
            <span>User-controlled disconnect</span>
          </div>
        </div>
      </section>

      <section className="public-section" id="features">
        <span className="eyebrow">FEATURES</span>
        <h2>Built around explicit user authorization.</h2>
        <div className="feature-grid">
          <article>
            <h3>Account connection</h3>
            <p>Connect each account separately through TikTok Login Kit.</p>
          </article>
          <article>
            <h3>Profile synchronization</h3>
            <p>Retrieve the authorized account's display name and avatar.</p>
          </article>
          <article>
            <h3>Token lifecycle</h3>
            <p>Refresh authorized access server-side without exposing tokens in the browser.</p>
          </article>
          <article>
            <h3>Audit history</h3>
            <p>Track account connection, profile sync, refresh, and disconnect events.</p>
          </article>
        </div>
      </section>

      <section className="public-section split-section" id="security">
        <div>
          <span className="eyebrow">SECURITY</span>
          <h2>Credentials stay on the server.</h2>
        </div>
        <div>
          <p>
            Access and refresh tokens are stored server-side in encrypted form. OAuth
            authorization codes and state values are not written to application access logs.
            Administrative sessions are server-backed and use HttpOnly cookies.
          </p>
          <p>
            Connected users can revoke the application's TikTok authorization by using the
            disconnect action. The application only requests permissions required by the
            implemented features.
          </p>
        </div>
      </section>

      <section className="public-section legal-callout">
        <div>
          <span className="eyebrow">TRANSPARENCY</span>
          <h2>Read the policies before connecting an account.</h2>
        </div>
        <div className="hero-actions">
          <a className="button-link" href="/privacy">Privacy Policy</a>
          <a className="button-link secondary" href="/terms">Terms of Service</a>
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
        <span className="eyebrow">LEGAL</span>
        <h1>Terms of Service</h1>
        <p className="legal-date">Effective date: {EFFECTIVE_DATE}</p>

        <h2>1. Service</h2>
        <p>
          TH TikTok Manager provides tools for users to connect TikTok accounts they are
          authorized to control, view basic account information, maintain OAuth connections,
          and revoke those connections. Access to TikTok features is subject to TikTok's own
          terms, policies, availability, and approval requirements.
        </p>

        <h2>2. Authorized use</h2>
        <p>
          You may use the service only with accounts and data you are authorized to access.
          You must not use the service to impersonate others, violate applicable law, bypass
          platform controls, or interfere with TikTok or other systems.
        </p>

        <h2>3. Account authorization</h2>
        <p>
          TikTok account access is granted through TikTok's OAuth authorization flow. The
          service does not require your TikTok password. You are responsible for reviewing
          the permissions shown by TikTok before authorizing access.
        </p>

        <h2>4. Availability</h2>
        <p>
          Features may change or become unavailable when TikTok changes its APIs, permissions,
          review status, rate limits, or platform requirements. The service is provided on an
          as-available basis and may be interrupted for maintenance or security reasons.
        </p>

        <h2>5. Security responsibilities</h2>
        <p>
          You are responsible for protecting your own administrator credentials and devices.
          Report suspected unauthorized access promptly and disconnect affected integrations
          when appropriate.
        </p>

        <h2>6. Termination and disconnect</h2>
        <p>
          You may disconnect a connected TikTok account from the control plane. Access may
          also be suspended when authorization expires, is revoked, or no longer satisfies
          TikTok's requirements.
        </p>

        <h2>7. Privacy</h2>
        <p>
          The collection and use of information through this service is described in the
          <a href="/privacy"> Privacy Policy</a>.
        </p>

        <h2>8. Changes</h2>
        <p>
          These Terms may be updated when the service or applicable platform requirements
          change. The effective date shown above identifies the current version.
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
        <span className="eyebrow">LEGAL</span>
        <h1>Privacy Policy</h1>
        <p className="legal-date">Effective date: {EFFECTIVE_DATE}</p>

        <h2>1. Information processed</h2>
        <p>
          When a user authorizes TikTok access, the service may process the TikTok account
          identifier, display name, avatar URL, granted scopes, OAuth access token, refresh
          token, token expiration times, connection status, and synchronization timestamps.
          Administrative login and account-management events are also recorded for security
          and operational auditing.
        </p>

        <h2>2. How information is obtained</h2>
        <p>
          TikTok account information is obtained through TikTok's official OAuth and API
          interfaces after the user grants permission. The service does not collect a user's
          TikTok password.
        </p>

        <h2>3. Purposes</h2>
        <p>
          Information is used to maintain authorized account connections, display basic
          profile information, refresh permitted access, support disconnect/revocation,
          diagnose service health, and maintain a security audit trail.
        </p>

        <h2>4. Storage and security</h2>
        <p>
          OAuth access and refresh tokens are stored on the server in encrypted form.
          Authorization codes, OAuth state values, raw tokens, and administrator passwords
          are not intentionally exposed in the application UI or written to application
          access logs. Administrative sessions use server-backed records and HttpOnly cookies.
        </p>

        <h2>5. Sharing</h2>
        <p>
          The service sends information to TikTok only as necessary to perform the authorized
          API operations requested by the user. The service does not intentionally sell TikTok
          OAuth tokens or connected-account profile data.
        </p>

        <h2>6. Retention</h2>
        <p>
          Connection records are retained while needed to operate the authorized integration
          and maintain security history. Expired OAuth state records are automatically cleaned.
          Operational backups and audit records may be retained for limited security and
          recovery purposes.
        </p>

        <h2>7. User controls</h2>
        <p>
          A connected account can be disconnected from the admin control plane, which requests
          revocation of the current TikTok authorization. Users may also manage permissions
          through TikTok where those controls are available.
        </p>

        <h2>8. Changes</h2>
        <p>
          This policy may be updated when service functionality or platform requirements
          change. The effective date above identifies the current version.
        </p>
      </article>
      <SiteFooter />
    </main>
  );
}
