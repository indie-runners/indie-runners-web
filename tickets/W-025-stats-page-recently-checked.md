# W-025 — A stats page: recently checked events, a 30-day rollup, a stable headline

`priority: 2` (raised from 4 by Paulo, 2026-10-22) · `effort: M` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-09-01 "A stats page" items 1–2 (scraper PM triage, Paulo's ask); denominator decided by Paulo 2026-10-21`

## The ask

Paulo: *"sort of a live blog of what is happening, so that users know
that there is movement in the back."* A new public page with three parts.
The map (item 3) is W-025's sibling, **W-026**, and goes on this page.

## The decision this ticket inherits (Paulo, 2026-10-21)

**Two numbers, each labelled, never mixed:**

| Part | Counts | Source |
|---|---|---|
| Headline | "N events tracked" | `core.events`, stable all year |
| Rollup | "N events checked in the last 30 days" | `event_last_checked_at` on the view |
| Map (W-026) | "Upcoming events by country" | the serving view |

The label is part of the acceptance. An unlabelled count is the exact
failure the IDEAS entry warns about.

## Rules quoted from the IDEAS entry (measured there, not re-derived)

- **A list of the last N, with no age filter**, so it is never empty.
  Successful runs are bursty: 11 of 30 days had zero, and the longest gap
  was 9d 18h. So a relative timestamp is not the primary framing.
- **"Last checked", not "last verified"**: 62% of successful runs are
  gate-shut. Event level only, never a per-field badge.
- **Never show run counters** (`questions_answered`, `error_message`, …).
  Event name and a timestamp are all of it.
- **`event_last_checked_at` is `timestamp with time zone`.** Bind it
  `DateTime`, not `Text`. The neighbouring `event_last_scraped_at` *is*
  text, and the two look alike. Not mapped in `core.py` yet.
- **Do not use `events.updated_at` / `races.updated_at`.** Corpus-wide
  upserts make them mean "the corpus was rebuilt".

## What the developer settles (name each)

1. **Which `core.events` rows count as "tracked"**, with one read-only
   query. Is it all rows, or `status = 'active'`? Say which, and put the
   number and date in the close-out.
2. **N for the list**, and what each row links to. It must not link to a
   404 (the W-019 lesson). The list reads the view, so its events
   resolve.
3. **The URL and how it is reached** (footer link, nav, neither). Keep
   it small.

## Acceptance

1. Page renders **anon** (it is public) and signed-in, with all three
   labels visible.
2. The list is non-empty and newest first, showing name and "last
   checked" date only.
3. The rollup and headline match a read-only count run the same day,
   both quoted in the close-out.
4. **Query cost:** a handful of aggregate queries per request, with no
   per-row queries. Say whether it needs caching at 300 to 500 events,
   and why.
5. `HEAD` answers like `GET` (W-005's contract). `docs/FILE_TREE.md` and
   the changelog updated.

## Out of scope

- The map (W-026).
- Per-field freshness, run outcomes, error rates.
- `robots.txt` / `sitemap.xml` treatment of the new page (W-006 / W-010).

## Verdict

**VERDICT: APPROVED** — 2026-10-23. Every acceptance item met. Verified
by the developer on `localhost:8010`, anon and signed-in (minted session
cookie, which the server cannot tell from an OAuth sign-in). The W-009
question answers itself: `/stats` 404s on master, so a 200 showing `491`
proves the branch was the checkout served. Ticket is `deploy: batched`.
Note: W-022's branch also claims changelog 1.9.14; whichever merges
second renumbers.

**Not verified:**
- "Dates render in UTC" is asserted, not measured. The date prints in the
  Postgres session `TimeZone` psycopg returns; nothing in `app/db.py` sets
  it. Date only, so the worst case is one day off near midnight. Settled
  by `SHOW TimeZone` on the app's connection.
- The template's no-link branch (`Unknown event`) has never rendered:
  0 of 385 view events have a NULL slug or year.
- `core.py`'s "every row of an event carries the same value" comes from
  the scraper, not a measurement here. `max()` is correct either way.
- The footer's fourth link at phone width.
