# W-035 — The legal pages link a signed-out reader to a raw JSON 401

`priority: 2` · `effort: S` · `area: services` · `deploy: batched`
`source: W-034 review, 2026-10-23`

## What is wrong

Privacy §8 (W-022, merged) and terms §9 (W-034) both link
`<a href="/settings">Settings → Delete account</a>`. Those are public
pages, mostly read signed out. `/settings` depends on
`get_required_user` (`app/main.py:112-115`):

```python
if user is None:
    raise HTTPException(status_code=401, detail="not authenticated")
```

The app has no exception handler, so a signed-out reader who follows the
link gets FastAPI's bare `{"detail":"not authenticated"}`. W-034's
changelog saw it ("Anon `/settings` is 401, as before"). Before W-022,
every `/settings` link sat on a signed-in page, so nobody signed out
could reach it. The W-022 review missed this too.

`/profile`, `/crews/new` and `/me` behave the same way. Nothing public
links to them today.

The app already has the pattern. The crew invite route (`main.py:736-738`)
stashes `post_login_redirect` and sends a signed-out visitor through
`/auth/google`.

## Acceptance

1. Signed out, following the §8 or §9 link lands on Google sign-in,
   then back on `/settings`. It never shows a JSON body.
2. The developer says whether the fix covers the other three GET routes
   or `/settings` alone, and why.
3. POST routes still refuse a signed-out request with an error status,
   not a redirect: `POST /settings/delete-account` stays `401` (routed
   check 9 reads it).
4. Checked in a browser, signed out and signed in.

## Out of scope

- The `#delete-account` anchor (IDEAS, 2026-10-23).
- A styled error page for other statuses.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-036** — 2026-10-23, on
`bbd20d9`. The branch row says `review`. Docs budget: 36. Merges into
master without conflict.

Acceptance 1–3 are met, judging from the diff and the changelog. Signed
out, `GET`/`HEAD /settings` returns 303 to `/auth/google?next=/settings`.
That goes through the existing `_validate_next` and the session key. The
two POSTs keep `get_required_user` and still return 401. That is what
routed check 9 reads. The scope call holds (acceptance 2): `/profile`
is linked only from the signed-in nav dropdown, `/crews/new` only from
`settings.html`, and `/me` is JSON, where a 401 is the right answer. The
dev server was run from the worktree, with `/proc/<pid>/cwd` checked.

**Acceptance 4 was not met as written.** The developer used curl, not a
browser, and says so. I did not block on it. The step nobody ran is the
callback popping `post_login_redirect`. This diff does not touch that
code, and the event page's sign-in buttons run it in production today.

**W-036 (follow-up):** `ARCHITECTURE.md:238` and the callback comment
(`main.py:851-853`) both say there is no `?next=` parameter and so no
open-redirect surface. `ARCHITECTURE.md:169` and the code say there is
one, with validation. This branch is now the third user of `?next=`.
Both stale claims are older than W-035.

**Merge order:** this branch claims 1.9.16. W-025 also needs a number
above 1.9.15. Whichever merges second takes 1.9.17.

**Not verified:**
- The full Google round trip in a browser, signed out → Google →
  `/settings`. Settled by one real click on the privacy §8 link after
  deploy, by Paulo.
- A stale session, i.e. a cookie whose `user_id` was deleted (W-022). It
  should take the same 303 path, because `get_current_user` returns
  `None`. Read from the code, not run.
