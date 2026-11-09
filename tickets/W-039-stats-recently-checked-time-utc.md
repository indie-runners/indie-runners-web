# W-039 — "Recently checked" shows a date only, and the zone it's in is never set

`priority: 2` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-23 (Paulo, high priority: "close the stats-page topic soon")`

## What is wrong

Paulo wants the time on each "Recently checked" row, in **UTC, labelled**
(his decision, `docs/IDEAS.md`):

> Paulo: *"it would be great to include timestamps to the recently
> checked."* Clock decided by Paulo: **UTC**, labelled.

`app/templates/stats.html:24` (master):

> `— last checked {{ e.checked_at.strftime('%-d %b %Y') }}`

The value is `max(event_last_checked_at)` (`app/main.py:826`), a
`timestamptz`. psycopg returns it as an aware datetime in the DB
session's `TimeZone`, and nothing in `app/db.py` sets that. W-025's
verdict left this open:

> **Not verified:**
> - "Dates render in UTC" is asserted, not measured. The date prints in the
>   Postgres session `TimeZone` psycopg returns; nothing in `app/db.py` sets

A date hides a wrong zone most of the time. A time shows it on every row.
So the time and the explicit conversion have to ship together.

## Acceptance

1. Each "Recently checked" row shows date and time, labelled UTC, for
   example `24 Oct 2026, 11:38 UTC`. The developer picks the format.
2. The conversion to UTC is done in code (`astimezone(timezone.utc)` or
   equivalent). It does not rely on the session `TimeZone`.
3. Evidence quoted in the changelog: one row's rendered time next to the
   same event's `event_last_checked_at` read with `AT TIME ZONE 'UTC'`
   in a read-only session. This closes W-025's open "renders in UTC".
4. `/stats` checked anon and signed in. The page does not branch on
   tier, but the brief asks for both.

## Out of scope

- The 30-day count's `since` boundary. It is a count, and a few hours
  of zone drift doesn't change what it means.
- W-037 (index 60 cap) and W-038 (ARCHITECTURE stats section). Those
  are the other two open stats items. They are not this one.
- Setting `TimeZone` on the connection in `app/db.py`. It would change
  every timestamp the app reads, which is a separate decision.

## Verdict

**VERDICT: APPROVED** — 2026-10-24. Two lines of code. `checked_at` is
`max()` of a `DateTime(timezone=True)` column filtered `isnot(None)`, so
`astimezone` always gets an aware value, never a naive one or `None`.
The changelog gives the wrong belief, the new one and the evidence, and
the evidence actually separates them: under `PGTZ=Europe/Berlin` the
branch still printed `12:19 UTC`, matching `AT TIME ZONE 'UTC'`.
Verified on `localhost:8039`, and `/proc/<pid>/cwd` named `irw-W039`, so
the W-009 trap is ruled out. Rendered anon and signed in. ARCHITECTURE
makes no UTC claim, so it needs no edit. Docs +37. Ticket is
`deploy: batched`. Routed check 13.

**Not verified:**
- The session `TimeZone` was measured through the local proxy, not from
  Cloud Run's `/cloudsql` socket. `deploy.sh` sets no `PGTZ`, so it should
  be the same, but since the fix makes the display independent of the
  zone, only the claim "production values don't change" rests on it.
  Check 13 reads it.
- Phone width. The row is about 12 characters longer, and a list item
  wraps, so the risk is low.
