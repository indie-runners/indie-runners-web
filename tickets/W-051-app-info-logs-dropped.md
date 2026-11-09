# W-051 — Every `logger.info` in `app/` is dropped before it reaches Cloud Logging

`priority: 4` · `effort: S` · `area: services` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-26 (while on W-032); verified at the W-032 review`

## What is wrong

Nothing in `app/` configures logging, and the Dockerfile runs plain
`uvicorn`. So the root logger stays at WARNING, and every module logger
(`logging.getLogger(__name__)` in `main.py` and all eight services)
drops its INFO lines. The only lines the service writes are uvicorn's
own, plus app warnings and errors.

## Evidence

The developer's note:

> 30 days of `indie-runners-web` logs hold no `Loaded N dedicated event
> slugs` (main.py:51, every cold start) and no `Deleted account`, but
> uvicorn's own access lines are there. The request log keeps when an
> account was deleted (a 303 on `POST /settings/delete-account`), not whose.

The W-032 review confirmed it:

> nothing in `app/` configures logging, the Dockerfile runs plain
> `uvicorn`, and so the root logger stays at WARNING and `delete_account`'s
> INFO line is dropped.

## The catch: turning INFO on starts logging user ids

Some of these lines carry a user id: `main.py:272` (`Rendering index
page for user {id}`, on every signed-in `/`), `delete_account`, and
`create_crew`. `privacy.html`'s "Server logs" paragraph promises only
"request metadata including IP address, user agent, timestamp, and
requested URL". A fix that only flips the level would leave the privacy
page wrong (the W-034 class of defect).

## Acceptance

1. App INFO lines reach stdout under uvicorn. Run locally,
   `bash scripts/dev.sh` prints `Loaded N dedicated event slugs` at
   startup.
2. The changelog lists every INFO line this turns on (`grep -rn
   'logger.info' app/`) and says, for each one, whether it was kept,
   demoted to DEBUG, or reworded. Per-request lines (`main.py:272`, `:494`,
   `:926` health check) are kept only with a stated reason.
3. If any kept line carries a user id, the "Server logs" paragraph in
   `privacy.html` says so, or the line drops the id. If changing the
   privacy text needs Paulo's sign-off, the ticket stops there and asks.
4. Both tiers still render (the change is at startup, so a bad config
   breaks every page).

AMENDED 2026-11-04 (triage), AUDIT_20261104T0705 on W-094's refusal line:

> the entry has no `severity` field. Cloud Logging records it as blank
> (DEFAULT), `logName` `run.googleapis.com%2Fstderr`. That is why the
> `severity>=ERROR` query in the brief never shows it

Same root cause: nothing configures logging. So the sweep's "no
ERROR-severity entry" covers request-log 5xx only, never an app line.

5. App log lines carry their level as a Cloud Logging severity: under
   the deployed revision, one `logger.warning` line reads `WARNING`.
   Locally, show the line as written to stdout.

## Out of scope

- Logging deletions *so they can be re-applied after a restore*. W-032
  ruled that out ("its own ticket and probably needs DDL"), and this
  ticket does not reopen it.
- Log-based metrics and alerting. Structured output is in scope only
  as far as acceptance 5 needs it.
- Uvicorn's access log format.
