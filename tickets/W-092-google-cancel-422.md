# W-092 — Cancelling Google sign-in lands on a raw JSON 422

`priority: 2` · `effort: S` · `area: routing` · `deploy: immediate`
`source: AUDIT_20261102T1131 F2`

**THE NEXT TICKET** (Paulo, 2026-11-02), ahead of W-080 and the crews arc.

## What is wrong

`google_callback` requires `code`. When Google redirects back without
one, FastAPI fails validation and answers its JSON 422 body. Google
does exactly that when someone clicks Cancel on the consent screen: it
sends `error=access_denied` and no `code`. The visitor reaches a dead
end at the moment they were deciding whether to join.

## Evidence

From the audit, request log, 24h to 2026-11-02T11:31Z:

```
2026-11-01T19:43:00Z GET /auth/google/callback?error=access_denied 422  Firefox/Android
2026-11-01T16:28:09Z GET /auth/google/callback?error=access_denied 422  CriOS/iPhone
2026-11-01T15:17:14Z GET /auth/google/callback?error=access_denied 422  Chrome/Android
app/main.py:1046  async def google_callback(request: Request, code: str, db: Session = Depends(get_db))
```

Mechanism confirmed by the PM from source, `master` at d7769e3. Three
people in a day, all mobile. Whether any came back, the log cannot say.

The PM also found this from source: `main.py:845` queues
`post_login_redirect` from an invite landing before bouncing to Google.
On a cancel the key stays in the session cookie. A later, unrelated
sign-in then lands on that stale invite.

## Acceptance

1. A callback with no `code`, whatever else it carries, redirects to
   `/` with a `303`, the code base's existing status for this redirect
   (`main.py:846`). Check both against `scripts/dev.sh`:
   `curl -si 'localhost:8000/auth/google/callback?error=access_denied'`
   and the same with no query. Neither returns `422`.
2. That path pops `post_login_redirect` from the session.
3. A signed-in session hitting the same URL stays signed in. `user_id`
   is untouched. This is the signed-in tier's check.
4. A real Cancel on Google's consent screen, run locally, lands on the
   homepage signed out.
5. Changelog: the wrong belief is that Google always returns a `code`
   to the callback.

**Why `/` and not back where they came from:** `/settings` and invite
URLs are signed-in pages that send an anonymous visitor straight back to
Google. Returning there after a cancel loops.

## Out of scope

- **A message saying sign-in was cancelled.** The app has no flash
  mechanism, and building one is a feature, not this fix.
- **A `code` that fails the token exchange.** That is a different
  failure with a different symptom, and nothing in the log shows it.
- **The `HEAD` arm** beyond it not returning an error.
- **OAuth `state` handling.** Not raised by this finding.

## Review — 2026-11-02

Branch `fix/google-cancel-callback-422` at `c6ee402`. The code does what
the spec asks, in the right place. Every acceptance item has a run
behind it, including Paulo's real Cancel against the worktree's server,
and the run was pinned to the worktree with `/proc/<pid>/cwd`, as W-009
requires. Docs: 44 added lines. 1.9.59, ARCHITECTURE updated, no file
added.

**R1 (blocks) — the changelog's new belief overstates its scope.**

```
- **New belief: a callback without a `code` is a cancel.**
```

Cancel is one way to get there. Google's error redirect can carry other
`error` values, among them `invalid_scope`, `unauthorized_client`,
`server_error` and `temporarily_unavailable`. Sending all of them home
is right; calling them all a cancel is not. The person who inherits this
sentence is whoever builds the "sign-in cancelled" notice this ticket
leaves out. They would tell a visitor Google refused that they
cancelled. **Fix:** reword it to say a callback without a `code` is a
sign-in that did not complete, a cancel (`access_denied`) or an error
Google reports, and all of them go home. The code comment and the
ARCHITECTURE line are already scoped correctly. Nothing else changes.

**Watched, not ticketed.** A configuration error that refuses every
sign-in now ends as a quiet `303 /` where it used to be a loud `422`.
The `error=` value stays in the request URL, so routed check 43 reads
it. The success path answers `307`, so the two can be told apart.

**For triage, not this branch:** the developer's drive-by, where a
`code` that fails the exchange is a 500.

## Verdict

**VERDICT: BLOCKED — R1** — 2026-11-02. One changelog sentence; no code
change. Ticket is `deploy: immediate`. Routed check 43 written.

**Not verified:** whether the three visitors on 2026-11-01 cancelled by
choice or were refused by Google. The log shows only `access_denied`.
Paulo's Cancel ran against localhost, not the production redirect URI.
Check 43 settles that on the first sweep with a callback `303`.

## Re-review — 2026-11-02

Branch at `3b00549`. Since `c6ee402` the only change is the changelog's
new belief: a callback without a `code` is a sign-in that did not
complete, a cancel or an error Google reports, and none is assumed to be
a cancel. **R1 resolved.** No code changed, so the earlier runs still
stand. Docs: 46 added lines. Routed check 43 stands as written.

**VERDICT: APPROVED** — 2026-11-02. Ticket is `deploy: immediate`.

**Not verified:** unchanged from the review above. Whether the
2026-11-01 visitors cancelled by choice, and the cancel path against the
production redirect URI. Check 43 settles the second.
