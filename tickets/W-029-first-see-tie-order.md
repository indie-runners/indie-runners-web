# W-029 — A tile's location and terrain depend on Postgres's tie order

`priority: 4` · `effort: S` · `area: services` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-22 (while on W-020), filed at the W-020 review`

## What is wrong

`list_races` orders rows by `sort_key` alone (`race_service.py`,
`order_by(sort_key.asc())`). The grouping loop takes location, terrain,
`race_status` and W-016's mixed-currency price from the **first row
seen**. When an event has two races on its earliest date, Postgres
picks which row comes first, and that choice changes with the query
plan. From the developer's note:

> Measured: under `date_from=2027-01-01`, 24 non-TBC events showed
> different first-see fields after W-020 added a predicate, every one
> with a tie at its earliest date.

So the same event's tile can show a different location or terrain
depending on which filters are set. ARCHITECTURE already records the
same tie-break as the cause of an 11-event SQL/Python disagreement on
location (lines 67-76).

## Acceptance

1. A secondary `ORDER BY` key makes row order total. **Default: the
   race's primary key**, which is stable and makes no product claim. If
   the developer thinks a meaningful key fits better (for example, the
   longest race first), say so in TODO before building it. That choice
   is Paulo's.
2. Re-run the developer's comparison: the first-see fields of every
   event match between no filter and `date_from=2027-01-01`.
3. ARCHITECTURE's location paragraph says ties are now broken by the
   named key.
4. Changelog entry.

## Out of scope

- Replacing first-see with an aggregate for location or terrain. That
  is a different, larger decision.
- `core.*`.

## Review — 2026-10-26

The code is right and minimal. `mv_id` is `uuid_generate_v5(event_id-race_id-occurrence_id)`
(scraper migration 075, `base_data`), so the tie-break is deterministic across MV refreshes. It
moves only when an occurrence rolls over to its next edition. The changelog carries the wrong
belief, the cost, the new belief and the evidence. Verification ran the worktree's own code
(`:8050`, cwd checked), with both tiers on both URLs. TBC events are in the comparison. Docs diff
is 50 lines.

**R1 — the docs claim filter-invariance; the fix delivers plan-invariance.** ARCHITECTURE:
"the first row seen no longer depends on the query plan **or the filters set**". Changelog
heading: "a tile's location and terrain **no longer change with the filters**". `list_races`
filters per race before grouping. `date_from`/`date_to` drop an event's races outside the range,
and `search` matches `race_location` and `terrain_type`. So `?search=Esperanza` on
`tenerife_bluetrail` keeps only the La Esperanza race and the tile reads La Esperanza, while `/`
reads Playa de los Cristianos. That is by design, not a defect. The changelog's own measurement
is scoped correctly ("events … the filter keeps whole"). The two sentences are what a future
reader inherits, and both read universally. Fix: say that for the same set of surviving rows the
pick no longer depends on the plan, and that a filter that drops some of an event's races still
changes the pick. Prose only, no code change.

Not blocking, not mine to ticket: the developer's DEV_NOTES entry (a tile shows "—" where the
`mv_id`-first tied race has no location and the profile names a town, `otf_presented_by`). It is
on the branch, so it reaches master with the merge. Triage disposes of it then.

## Verdict

**VERDICT: BLOCKED — R1** — 2026-10-26. The routed check gets written at re-review, when the
verdict predicts production.

**Not verified:** the 20 → 0 and 31 → 0 comparison was not re-run by me. I read it from the
changelog. Neither was the claim that 46 of 381 default tiles change; that is the deploy's
user-visible effect.

## Re-review — 2026-10-26

R1 resolved in `f148dce`. ARCHITECTURE now reads "for the same surviving rows the first one seen
no longer depends on the query plan. A filter that drops some of an event's races (dates, or
`search` on location/terrain) still changes it". The changelog heading is "no longer follow the
query plan", and its Scope sentence names `?search=Esperanza`. The developer ran that URL, and
the tile reads La Esperanza. No code changed since the first review. Docs diff is 55 lines.

**VERDICT: APPROVED** — 2026-10-26. `deploy: batched`. Routed check 25.

**Not verified:** the before/after comparison (20 → 0, 31 → 0), which I read from the changelog
and did not re-run. The 46 default tiles that change town or terrain on deploy were not looked at
one by one. Which tied race wins is arbitrary by design (the ticket's default key).
