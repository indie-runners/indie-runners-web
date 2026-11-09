# W-026 — Coverage map: upcoming events by country, on the stats page

`priority: 2` (raised from 4 by Paulo, 2026-10-22) · `effort: M` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-09-01 "A stats page" item 3; denominator decided by Paulo 2026-10-21`

**Depends on W-025** (the page it sits on).

## The ask and the decision

A map of events per country. **It counts upcoming events from the serving
view, labelled "Upcoming events by country".** Paulo chose this on
2026-10-21 so that every country click lands on a non-empty index. The
headline "events tracked" number lives in W-025 and is a different
denominator. Do not mix them.

## Facts from the IDEAS entry (measured 2026-09-01)

- **`core.events.country_code` is 100% NULL.** It is a trap. The view
  carries `event_country_alpha2` (ISO alpha-2, what a map library wants)
  and `event_country_code` (lowercased name). About 0.9% of rows are NULL.
- It is a `GROUP BY` over the view this app already serves. No migration.

## What the developer settles (name each)

1. **The rendering**: a vendored SVG, a small library, or a ranked list
   beside a simple map. **Do not add a heavy dependency for one map.**
   Name the choice and its weight.
2. **Count unit**: distinct events, not rows. A 10-race event counts once.
3. **Click target**: `/?country=<event_country_code>`. The index filter
   matches on that column with `ilike`. Check that a click on each listed
   country returns at least one tile.
4. **NULL-country events**: not on the map. Say how many, in the
   close-out.

## Acceptance

1. Map renders anon and signed-in, labelled. A country with zero
   upcoming events reads as empty and is not clickable.
2. Counts match a read-only `GROUP BY` run the same day (quoted).
3. Every clickable country lands on a non-empty index. Spot-check three,
   including one small one.
4. Usable at phone width. Keyboard and screen-reader users can get the
   counts (a list fallback is fine).
5. Changelog entry, and `docs/FILE_TREE.md` if assets are added.

## Out of scope

- Scraper target counts per country (`race_scraper.*` is not reachable
  from this app).
- Region or city granularity, and time sliders.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-037, W-038** — 2026-10-23. Every
acceptance item met. The developer counted over `list_races` instead of
the raw view, which departs from the letter of "from the serving view".
The reason is quoted (389 against 387, TBC rows past their expected
month), and it serves Paulo's stated purpose: every click lands on a
non-empty index. Verified by the developer on `localhost:8026`, with the
serving cwd checked (W-009), anon and signed-in (minted cookie), at
1200 px and 390 px. All 42 country links were curled. Ticket is
`deploy: batched`. Rendering: a vendored 43 KB JSON (9 KB gzipped), no
JS, no new dependency. 3 events have no country.

**Not verified:**
- Acceptance 2 asked for the `GROUP BY` to be quoted. The changelog says
  it matched at 2026-10-23T21:16Z, but the SQL is not in the branch, so
  the 42-count claim cannot be re-run from the record.
- "Non-empty by construction" holds only while `/stats` calls
  `list_races(RaceFilters())` with the same defaults as a bare `/`. A
  default predicate added to the index later would break it, and
  nothing would notice. Routed check 12 watches for that.
- The map assumes one `event_country_alpha2` per `event_country_code`.
  39 shaded = 42 listed − 3 outside Europe is consistent with that, but
  nobody has measured it (W-038).
- A country with a name but a NULL alpha2 (list only, not on the map)
  has never rendered.
- All of it ran against the dev database from a worktree, not
  production.
