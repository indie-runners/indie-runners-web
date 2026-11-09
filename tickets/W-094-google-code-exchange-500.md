# W-094 — A Google code that fails the token exchange is a raw 500

`priority: 2` · `effort: S` · `area: auth` · `deploy: immediate`
`source: AUDIT_20261103T0806 F2; docs/DEV_NOTES.md 2026-11-02 (while on W-092)`

## What is wrong

`google_callback` (`app/main.py`) hands any `code` to
`GoogleAuthService.exchange_code_for_token`, which calls
`response.raise_for_status()`. When Google refuses the code, the
`httpx.HTTPStatusError` escapes and the visitor gets a 500. W-092 closed
the no-`code` case only. A one-time code is refused whenever it is
replayed (reload, back button, double tap), so a sign-in that worked is
followed by an error page.

## Evidence

From the audit, verbatim:

```
2026-11-02T13:02:15.97Z  307  GET /auth/google/callback?code=4/0AUn6Hd-i4zf…   (sign-in completes)
2026-11-02T13:02:16.85Z  500  same URL, same code
2026-11-02T13:02:19.78Z  500  same URL, same code
2026-11-02T13:02:22.22Z  500  same URL, same code
  File "/app/app/services/auth_service.py", line 35, in exchange_code_for_token
    response.raise_for_status()
httpx.HTTPStatusError: Client error '400 Bad Request' for url 'https://oauth2.googleapis.com/token'
```

The only ERROR-severity entries in 24h. The developer saw the same path
while on W-092: `GET /auth/google/callback?code=bogus` is a 500.

## Acceptance

1. `GET /auth/google/callback?code=bogus` while **signed in** lands on
   `/` (or the queued `post_login_redirect`), session intact, no error
   shown. This is the replay case above.
2. The same request while **signed out** answers a 4xx page saying
   sign-in failed and offering to try again. Not a 500, and not a silent
   return home.
3. Each refused exchange writes **one log line at WARNING or above**
   carrying Google's `error` value (e.g. `invalid_grant`), never the code.
   INFO is dropped before Cloud Logging (W-051), so INFO does not count.
   Without this line, Google refusing every exchange (a bad client
   secret) would look like silence: that is site-down for sign-in.
4. A real sign-in still completes with `307`. Verified signed-in and
   signed-out, locally, with the log line shown.

## Out of scope

- A failure in `get_userinfo` after a good exchange. Same shape, never
  seen in the log. Note it in DEV_NOTES if you touch it.
- Retries, a `state` parameter, any change to W-092's no-`code` branch.
- W-051 (configuring INFO logging).

**At review:** the PM routes a check. Its gate is the image digest that
carries this change, not "the first revision after merge" (check 44
gated on a revision that carried the old image).

## Verdict

**VERDICT: APPROVED** — 2026-11-03. Branch `fix/google-code-exchange-500`
(`c7842a2`, `0de1427`), changelog 1.9.61. Changelog names the wrong belief,
its cost and the evidence; the severity claim was scoped to what was run.
"Try again" goes to `/auth/google` with no `next`, which leaves the queued
redirect alone, so the retry lands where the visitor was going. Docs diff 60
lines. `deploy: immediate`. Routed as check 45.

A Google **5xx** on the token endpoint also becomes `CodeExchangeRefused`
(`response.is_error`): a quiet redirect if signed in, the 400 page if not. A
better outcome than a 500; the log line then carries a number, not an
`error` string, and check 45 reads it that way.

**Not verified:**
- A real code replayed. Paulo's back button re-entered `/auth/google`, so
  `?code=bogus` stands in (same endpoint, same `invalid_grant`). Settled by
  the first production replay under check 45.
- A replay that arrives before the first response's cookie (a double tap):
  the session has no `user_id` yet, so a person who is in fact signed in
  sees the 400 page. Never run. Harmless if it happens: Try again works.
- Google 5xx, and what severity Cloud Logging gives the WARNING line
  (Python's last-resort handler, W-051). Check 45 records it.
- The 400 page was checked by its HTML in curl, not looked at in a browser.
  It is `event_not_found.html`'s shell with existing classes.
- The developer's two drive-bys (Google unreachable, `get_userinfo` 4xx)
  are still 500s, out of this ticket's scope; next triage.
