# W-069 — Three pages name an event's location three ways

**SUPERSEDED 2026-10-28 — folded into W-070** (Paulo's cascade: HQ, else first race with a town, one shared read, not gated). Kept for the evidence. Don't take it.

`priority: 4` · `effort: S` · `area: services` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-27 (while on W-013), Paulo's ruling in it`

## GATED — on the scraper

Waits until `event_location` is populated in
`core.v_denormalized_event_data_upcoming`. Routed to the scraper's
`docs/IDEAS.md` 2026-10-28 (scraper T-039 holds the column). Today it is
populated on 0 of 396 events (read-only query,
2026-10-28). Don't start before a sweep or query shows it populated.

## What is wrong

From the developer's note, with Paulo's ruling:

> **Paulo, 2026-10-27:** the scraper should work out an event location.
> `race_location` asks for a race's start, and the event's HQ can be
> somewhere else. Not a web workaround: don't fall back to a race town
> here. **And every place that names an event's location must agree**
> (Paulo): today the event hero (`event_location`, always empty), the home
> tile (first-see row's `race_location`, `race_service.py:242`) and the
> profile's race calendar (earliest-dated race's `race_location`,
> `profile_service.py:172-177`) are three different reads. The calendar
> shows Transgrancanaria in "Artenara", one race's start, not the
> Maspalomas HQ. When the scraper populates `event_location`, the web
> ticket that follows moves all three onto it.

## Acceptance

1. Hero, tile and profile calendar read `event_location`, one shared
   read. A row where it is NULL shows the same empty state in all three.
2. Transgrancanaria (or another event whose HQ differs from a race start)
   shows the same town in all three, quoted in the changelog.
3. ARCHITECTURE says where an event's location comes from.

## Out of scope

- Race-level locations on the event page's race list (those are race starts).
- W-055 is the interim tile fix. This ticket supersedes it on the tile;
  if W-055 has merged, remove its fallback here.
