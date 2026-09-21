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
          <h2>Official account authorization</h2>
          <p>
            Users authorize access on TikTok. The service does not request or collect
            TikTok passwords. Features are activated only when the application has the
            corresponding TikTok product approval and the user grants the required scope.
          </p>
          <div className="public-facts">
            <span>OAuth 2.0 authorization</span>
            <span>Profile and analytics tools</span>
            <span>Video library and publishing workflows</span>
            <span>Server-side token storage</span>
          </div>
        </div>
      </section>

      <section className="public-section" id="features">
        <span className="eyebrow">FEATURES</span>
        <h2>Built around explicit user authorization.</h2>
        <div className="feature-grid">
          <article>
            <h3>Account connection</h3>
            <p>Connect each account separately through TikTok Login Kit and explicit consent.</p>
          </article>
          <article>
            <h3>Profile and statistics</h3>
            <p>
              Synchronize authorized profile fields and account statistics when the approved
              scopes are granted.
            </p>
          </article>
          <article>
            <h3>Video library and analytics</h3>
            <p>
              Read an authorized account's public videos, refresh metrics, and build historical
              performance snapshots when video access is approved.
            </p>
          </article>
          <article>
            <h3>Draft upload</h3>
            <p>
              Send authorized video or photo content to TikTok Inbox as a draft for the creator
              to finish editing and posting.
            </p>
          </article>
          <article>
            <h3>Direct Post and scheduling</h3>
            <p>
              Prepare Direct Post metadata, respect current creator settings, and schedule
              approved publishing jobs through the Content Posting API.
            </p>
          </article>
          <article>
            <h3>Operations and audit history</h3>
            <p>
              Monitor tokens, scopes, webhooks, publishing status, backups, and account events
              from one control plane.
            </p>
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
          authorized to control, synchronize permitted profile and analytics data, manage
          authorized public-video information, stage draft uploads, prepare Direct Post jobs,
          schedule publishing operations, maintain OAuth connections, and revoke those
          connections. Each feature depends on the TikTok products and scopes approved for the
          application and granted by the user. Access to TikTok features is subject to TikTok's
          own terms, policies, availability, and approval requirements.
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
          identifier, display name, avatar URL, additional profile fields, account statistics,
          public-video metadata and metrics, granted scopes, OAuth access token, refresh token,
          token expiration times, connection status, and synchronization timestamps when the
          corresponding permissions are granted. When a user uses content workflows, the
          service may also process staged media metadata, user-supplied photo URLs, captions,
          privacy and interaction selections, draft/direct-post job state, scheduling metadata,
          TikTok publish identifiers, public post identifiers, and webhook events.
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
          Information is used to maintain authorized account connections, display permitted
          profile and statistics, synchronize public-video data, build historical analytics,
          execute user-requested draft/direct-post workflows, operate publishing schedules,
          process TikTok webhook updates, refresh permitted access, support
          disconnect/revocation, diagnose service health, and maintain a security audit trail.
        </p>

        <h2>4. Storage and security</h2>
        <p>
          OAuth access and refresh tokens are stored on the server in encrypted form.
          Staged local media is stored server-side for the requested content workflow and is
          not exposed through the public website. Authorization codes, OAuth state values, raw
          tokens, and administrator passwords are not intentionally exposed in the application
          UI or written to application access logs. Administrative sessions use server-backed
          records and HttpOnly cookies.
        </p>

        <h2>5. Sharing</h2>
        <p>
          The service sends information to TikTok only as necessary to perform the authorized
          API operations requested by the user. The service does not intentionally sell TikTok
          OAuth tokens or connected-account profile data.
        </p>

        <h2>6. Retention</h2>
        <p>
          Connection, synchronization, publishing, webhook, and analytics records are
          retained while needed to operate the authorized integration and maintain security
          history. Staged media may be retained while required for a requested draft or
          publishing workflow and operational recovery. Expired OAuth state records are
          automatically cleaned. Operational backups and audit records may be retained for
          limited security and recovery purposes.
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
