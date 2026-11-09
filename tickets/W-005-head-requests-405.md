# W-005 — `HEAD` returns 405 on every public page, including `/`

`priority: 2` · `effort: S` · `area: routing` · `deploy: batched`
`source: exports/reports/AUDIT_20260828T0812.md` (F2)

## What is wrong

Every route in `app/main.py` is declared `@app.get` or `@app.post`. FastAPI's
`APIRoute` does **not** synthesise a `HEAD` handler for a `GET` route, so any
client that probes with `HEAD` before fetching gets a 405 — on the homepage
included.

The defect is not "one missing decorator". It is that the app's method surface
was never stated: `GET` was chosen per-route and `HEAD` was never considered, so
the site is unreachable to a whole class of client that never issues a `GET` at
all.

## Evidence

Confirmed live against the current revision, not inferred from logs:

```
HEAD / -> 405
GET  / -> 200
```

Production logs, real clients over the last week:

```
2026-08-27T09:14:18.979289Z	HEAD	405	https://indierunners.co/privacy	ShapBot/0.1.0
2026-08-27T09:14:14.970067Z	HEAD	405	https://indierunners.co/terms	ShapBot/0.1.0
2026-08-27T09:14:14.461661Z	HEAD	405	https://indierunners.co/imprint	ShapBot/0.1.0
2026-08-27T09:14:14.312047Z	HEAD	405	https://indierunners.co/auth/google	ShapBot/0.1.0
2026-08-27T09:14:13.048148Z	HEAD	405	https://indierunners.co/	ShapBot/0.1.0
2026-08-24T20:41:49.766088Z	HEAD	405	https://indierunners.co/	Mozilla/5.0 (X11; Linux x86_64) ... Chrome/96.0.4664.45
2026-08-21T19:23:45.935266Z	HEAD	405	https://indierunners.co/	Mozilla/5.0 (X11; Linux x86_64) ... Chrome/96.0.4664.45
```

The route declarations, verified in the working tree on `master`:

```
158:@app.get("/")
741:@app.get("/imprint")
750:@app.get("/privacy")
759:@app.get("/terms")
796:@app.get("/auth/google")
```

`grep -n "^@app\.head" app/main.py` returns nothing.

The `Chrome/96` agent hitting `HEAD /` on a regular cadence reads as an uptime
monitor. This is invisible to the audit's own site check because `curl` defaults
to `GET`.

## Why it matters

Nobody is locked out of the site today — that is why this is `batched`, not
`immediate`. The cost is that the service **looks down** to link checkers,
preview/unfurl bots and uptime monitors, and that any future uptime alerting
built on `HEAD` would be wrong from the day it was switched on.

## Acceptance

- `HEAD /` returns **200** with the same status and headers a `GET` would, and
  an empty body.
- The same holds for the other anon-reachable pages: `/imprint`, `/privacy`,
  `/terms`, and an event page `/events/{slug}/{year}`.
- `GET` behaviour on every route is unchanged — check a signed-in page and an
  anon page still render.
- The `POST`-only routes still reject `HEAD`. `HEAD /settings` must not be made
  to look like a successful read of a page that requires auth; whatever `GET`
  does for an anon user (redirect or 401), `HEAD` does the same.
- State in the changelog **which mechanism** was used and why. Adding
  `@app.head` beside each `@app.get` and switching to
  `@app.api_route(..., methods=["GET", "HEAD"])` are different trades — one is
  explicit per route, the other cannot drift out of sync. Pick one and name the
  reason; the wrong belief being corrected is "a GET route answers HEAD".

## Out of scope

- **The `POST` 405s from `wp2shell` and similar.** Those are hostile scans and
  are correctly rejected. Do not widen the method surface to silence them.
- **`/debug/health` and the `POST` endpoints.** Not part of the public browse
  surface; leave their methods alone.
- **Adding uptime monitoring.** This ticket makes `HEAD` correct so monitoring
  *could* be built on it. Building it is separate work.
- **Anything about `robots.txt` / `sitemap.xml`** — that is W-006, and shares
  only the "automated clients" theme, not the mechanism.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-009** — 2026-08-28. Merge now;
W-009 is on the board, not a condition.

Every acceptance criterion is met and the mechanism question the ticket
actually asked — `api_route` vs a stacked `@app.head` — is answered with a
reason that will still hold for whoever adds route seventeen: one
declaration cannot drift out of sync with itself. The changelog names the
wrong belief ("a `GET` route answers `HEAD`"), what it cost, and the
evidence, and it states the trade it accepted (a decorator that no longer
reads as the FastAPI idiom) rather than presenting the choice as free.

**Verified in review, statically, against the branch — no server started
and no DB session opened.** The route census confirms the changelog's
count exactly: 15 routes converted to `@app.api_route(..., methods=["GET",
"HEAD"])`, `/debug/health` alone keeping `@app.get`, `grep "@app.head"`
empty, and all five `@app.post` routes untouched. The auth claim checks
out at the source: `get_required_user` (`app/main.py:112-115`) raises
`HTTPException(401)` when the user is `None`, so `HEAD /settings`
anonymous is a 401 and not a 200 — the criterion most likely to have been
wrong, and it holds. `/profile` answering 307 in both tiers is
`profile_self`'s unconditional `RedirectResponse`, not a discrepancy.

**On the auth routes gaining `HEAD`, considered and deliberately not
blocked.** `HEAD /auth/logout` clears the session and `HEAD /auth/google`
writes `post_login_redirect` — a `HEAD` with a side effect looks alarming.
It is the ticket's own rule applied consistently: `HEAD` does exactly what
`GET` does for the same caller, and these were state-changing `GET`s
before this branch existed. That is pre-existing behaviour this diff
neither created nor worsened, and a prefetching client could always have
triggered it with a `GET`. Blocking here would be reviewing a design
decision this ticket did not take. If it is worth revisiting, it is a new
ticket about state-changing `GET`s, not a finding against W-005.

**Docs hygiene passes.** `CHANGELOG.md` bumped to 1.9.7;
`ARCHITECTURE.md` gains an "HTTP method surface" section stating the
contract, which is right — the defect was that the surface was never
stated, so recording the fix without recording the contract would leave
the next route free to reintroduce it. `FILE_TREE.md` correctly unchanged;
no file was added, moved or removed.

**W-009 amended rather than newly cut**, per the developer's own read in
`DEV_NOTES.md`, which asked the PM to choose. Both are `scripts/dev.sh`
declaring a service ready without checking, so they are one ticket. The
amendment carries the second mode in full, and re-titles and re-prioritises
to match: **p5 -> p4**, because this is no longer only local-tooling
comfort. A `dev.sh` that silently probes another checkout returns
*plausible* output from the wrong code, and in a repo with no test suite
(W-003) "verified in the browser" is the only evidence a review has — the
failure mode forges the artefact the review depends on. It was caught here
only because 405-vs-200 is maximally loud; a template or filter-boundary
ticket would not have been.

**Not verified:**

- **Nothing was re-run.** The review is static: the diff, the route
  census, and the source of `get_required_user`. Every runtime claim —
  `HEAD /` returning 200 with a zero-length body, the field-by-field
  header diff including `Content-Length: 152406`, `HEAD /debug/health`
  still 405, 60 event cards in each tier — rests on the developer's
  account in the 1.9.7 entry, which is detailed, internally consistent and
  explicit about its own gaps. Re-running it would have meant a server and
  a DB session against a shared 45-connection budget, and re-doing the
  developer's verification is not the gatekeeper's job.
- **The OAuth round trip.** `/auth/google` and `/auth/google/callback`
  both gained `HEAD`; only their method surface was checked, never the
  flow. The developer stated this plainly and it is carried here verbatim
  because a minted-cookie signed-in check invites exactly the wrong
  reading: it exercises the authenticated *render*, not the *sign-in*.
  `HEAD /auth/google/callback` without a `code` parameter was not probed —
  it should be a 422 from FastAPI's own validation, but that is inference,
  not a measurement.
- **`/me`, `/crews/*` and `/profile/{user_id}` were not probed** in either
  tier. They are the same one-line mechanical conversion as the routes
  that were, and the conversion is verified by the census rather than by
  request.
- **Nothing was checked against production.** This is a `batched` deploy
  and the fix is only observable to non-browser clients, so the real
  confirmation is the next sweep seeing `ShapBot` and the `Chrome/96`
  monitor take a 200 instead of a 405 on `/`. **For the auditor: that is
  this ticket's real test.**

**VERDICT: APPROVED WITH FOLLOW-UPS — W-009**
