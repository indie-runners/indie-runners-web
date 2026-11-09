# W-055 — A tile shows "—" for location when a sibling race has one

**SUPERSEDED 2026-10-28 — folded into W-070** (Paulo's cascade: HQ, else first race with a town, one shared read, not gated). Kept for the evidence. Don't take it.

`priority: 4` · `effort: S` · `area: services` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-26 (while on W-029)`

## What is wrong

The tile's location comes from whichever race is seen first, NULL or
not. The profile's location skips NULLs. So where the first-seen race
has no `race_location` but another race in the same event has one, the
tile renders "—" and the profile names a town. The data is there and the
tile does not show it.

## Evidence

The developer's note, verbatim:

> The tile now breaks ties by `mv_id`, like the profile, but the
> profile's location subquery skips `race_location IS NULL` and the tile's
> first-see does not. Where the `mv_id`-first tied row has no location, the tile
> shows "—" and the profile a town: `otf_presented_by` today (checked after the fix).

`app/services/race_service.py:242`, inside `if eid not in events:`,
which runs once per event, on the first row:

```
                    "location": r.race_location,
```

`app/services/profile_service.py:173-177`:

```
                    (SELECT v.race_location FROM core.mv_denormalized_event_data v
                      WHERE v.event_id = a.event_id::text AND v.race_location IS NOT NULL
                      ORDER BY v.occurrence_id IS NOT DISTINCT FROM a.occurrence_id::text DESC,
                               v.race_date NULLS LAST, v.mv_id
                      LIMIT 1) AS location,
```

`app/templates/partials/race_tile.html:69`: `{{ race.location or '—' }}`.

The mechanism is read from source. How many tiles it affects is not
measured.

## Acceptance

1. **Measure first, in one read-only session.** Count the events where
   the first-see row (`sort_key`, then `mv_id`) has a NULL
   `race_location` and some sibling row in the view has one. Quote the
   count and the query in the changelog.
2. The tile takes the first **non-NULL** `race_location` in the
   first-see order. An event where every race is NULL still shows "—".
3. ARCHITECTURE's location paragraph currently ends "though the profile
   skips a NULL `race_location` and the tile does not". It now states
   the rule both of them follow.
4. Render `/` anon and signed in. On the tile for `otf_presented_by`
   (or whatever event step 1 finds), the location shows a town, and it
   is the same town the profile row shows.

## Out of scope

- **Terrain.** The tile reads `terrain_type` first-see and the profile
  reads it longest-race-first, so the two already disagree by design
  (W-027). Step 1 may also count tiles with a NULL terrain where a
  sibling race has one. Report that number. Don't change terrain here.
- **Filters dropping races** (`search`, dates) still change the
  first-seen row. W-029 named that, and it stays.
- **The event page hero.** Not reported, and it reads its own fields.
