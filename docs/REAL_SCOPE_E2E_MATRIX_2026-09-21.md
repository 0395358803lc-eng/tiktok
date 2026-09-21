# Real-Scope E2E Acceptance Matrix

**Date:** 2026-09-21  
**Rule:** No scope is accepted from mocked API responses. A scope reaches LIVE PASS only after the Sandbox app is enabled for that scope, the target account grants it, TikTok returns real data/status, and the expected UI/database evidence is observed.

| Scope | Feature | Code | Current config/grant | Required LIVE evidence | Current result |
|---|---|---|---|---|---|
| `user.info.basic` | Login + basic identity | Implemented | Enabled + granted | OAuth callback succeeds; real account identity shown; tokens stored server-side | PASS |
| `user.info.profile` | Extended profile | Implemented | Not enabled/granted | Real username/bio/profile link/verification returned and persisted | BLOCKED |
| `user.info.stats` | Account stats + analytics | Implemented | Not enabled/granted | Real follower/following/likes/video counts returned; >=2 real snapshots produce delta | BLOCKED |
| `video.list` | Video Library | Implemented | Not enabled/granted | Real public video list returned; DB rows created; metadata refresh succeeds | BLOCKED |
| `video.upload` | Draft Upload | Implemented | Not enabled/granted | Real draft init succeeds; media transfer succeeds; status reaches TikTok Inbox | BLOCKED |
| `video.publish` | Direct Post | Implemented | Not enabled/granted | Creator Info real; SELF_ONLY test post initialized; status/webhook reaches completion | BLOCKED |

## Cross-cutting acceptance

### OAuth

PASS only when:

- state is one-time and not expired;
- callback succeeds using real TikTok authorization;
- token exchange returns HTTP success;
- account open_id matches;
- token refresh succeeds;
- disconnect/revoke behavior is verified.

### Webhooks

PASS only when:

- Developer Portal Test URL produces a real signed callback;
- callback returns HTTP 200;
- persisted event appears in Admin;
- duplicate delivery remains idempotent;
- at least one real Content Posting event is correlated by publish_id after posting scopes are enabled.

### Analytics

PASS only when:

- values come from TikTok APIs;
- no synthetic historical values are inserted;
- at least two observations exist before deltas/charts are treated as meaningful.

### Draft Upload

PASS only when:

- the account granted `video.upload`;
- TikTok returns a real `publish_id`;
- real file/photo source is accepted;
- status reaches `SEND_TO_USER_INBOX`;
- the creator can see the TikTok Inbox notification/draft.

### Direct Post

PASS only when:

- the account granted `video.publish`;
- real Creator Info is queried immediately before posting;
- privacy is user-selected;
- unavailable interactions cannot be enabled;
- explicit required consent is collected;
- unaudited client test respects TikTok visibility restrictions;
- real `publish_id` is returned;
- status/webhook completion is observed;
- system never retries post initialization after a `publish_id` exists.

### Scheduler

PASS only when:

- a future local time is converted to UTC;
- job remains SCHEDULED before due time;
- SchedulerWorker changes it to READY at/after due time;
- PublishWorker submits exactly once;
- cancel/reschedule is rejected once TikTok has a publish_id.

## Evidence to retain per live test

For each scope test retain:

- timestamp;
- Sandbox/Production environment;
- account internal ID;
- granted scope list;
- HTTP/result status without raw token values;
- relevant DB row identifiers;
- worker/audit event type;
- screenshot/video of the user-visible result;
- no access/refresh tokens in screenshots or logs.

## Stop conditions

Do not mark a scope PASS if:

- the API result is mocked;
- the scope is only present in code;
- the app is configured for the scope but the account did not grant it;
- TikTok returned an authorization/scope error;
- only local database/UI behavior was tested;
- the test bypassed TikTok Developer Portal restrictions.


## Automatic Review Package evidence gate

The Review Package must not infer LIVE PASS from an early/intermediate state.

- `user.info.basic`: requires a connected account with a successful profile sync and real basic identity data.
- `user.info.profile`: requires at least one persisted extended-profile field after sync.
- `user.info.stats`: requires at least two snapshots containing real statistic values; a single snapshot is insufficient for historical/delta evidence.
- `video.list`: requires persisted TikTok video rows plus a successful video sync/refresh audit event.
- `video.upload`: requires a real `publish_id` and job state `SEND_TO_USER_INBOX` or `PUBLISH_COMPLETE`; `SUBMITTED` alone is not PASS.
- `video.publish`: requires a real `publish_id`, `PUBLISH_COMPLETE`, and completed scheduler state; `SUBMITTED` alone is not PASS.
- Webhook database rows alone do not prove that TikTok Developer Portal Test URL was used. Portal evidence remains a manual verification item.

Overall review status uses three states:

1. `NOT_READY_FOR_REVIEW` — at least one automatic requirement is failing.
2. `READY_FOR_MANUAL_VERIFICATION` — automatic requirements pass, but Developer Portal/manual evidence still needs confirmation.
3. `READY_FOR_REVIEW` — no automatic failure and no outstanding manual verification item.
