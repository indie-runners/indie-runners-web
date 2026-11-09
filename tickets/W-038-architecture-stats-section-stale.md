# W-038 — ARCHITECTURE's stats section no longer describes `/stats`

`priority: 5` · `effort: S` · `area: docs` · `deploy: batched`
`source: W-026 review, 2026-10-23`

## What is wrong

W-026 (1.9.18) added the coverage map. It left `docs/ARCHITECTURE.md`'s
"Stats page" section unchanged, and two of that section's sentences are
now false:

> states **two counts that are never combined** (Paulo, 2026-10-21)

The page now has a third labelled number, "Upcoming events by country".
It is counted over `RaceService.list_races(RaceFilters())`, not the
view, because the view keeps TBC rows whose expected month has passed
(389 against 387 on 2026-10-23). That decision is recorded only in the
changelog.

> Three aggregate queries, ~7 ms.

The page now also runs `list_races` over the whole view, as an index
request does, plus a `DISTINCT` over `event_country_alpha2`. A reader
who trusts "~7 ms" will treat `/stats` as cheap.

The grain table (`ARCHITECTURE.md:54`) does not list
`event_country_alpha2`. It is now mapped, and the map reads it as one
value per `event_country_code`. Nothing here has measured that.

## Acceptance

1. The stats section names three denominators. It says the map counts
   what `/?country=` serves, and why that differs from the view.
2. The cost line is re-measured, with a date.
3. `event_country_alpha2` is in the grain table, or the section says why
   it is left out. If the developer measures it (one read-only session),
   they quote the query.

## Out of scope

- Any code change.
- Re-checking the rest of the grain table (W-011, W-014).
