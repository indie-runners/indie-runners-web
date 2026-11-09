# W-027 — The profile reads location and terrain from columns that are always NULL

`priority: 3` · `effort: S` · `area: services` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-21 (while on W-019)`

## What is wrong

`ProfileService._load_rows` reads `e.location` and `e.event_type` from
`core.events`. From the developer's note:

> **all 491 rows have both NULL**
> (`select count(location), count(event_type) from core.events` → 0, 0).
> So `profile.html`'s location line and terrain badge never render.

The template's branches for both have never fired. The same trap applies
to `core.events.country_code` (100% NULL, W-026): the scraper fills these
facts on the MV, not on `core.events`.

## Step 1 decides the shape

The MV (`core.mv_denormalized_event_data`) carries `race_location` and
`terrain_type`, and it keeps past rows the serving view drops (406 past
non-TBC rows on 2026-10-21). But it does **not** cover every attended
event: `berlin_marathon` has left it entirely (audit F6). Measure, with
one read-only query, how many attendance rows the MV can supply, and pick
one:

- **Read from the MV**, event-level. Say how the per-race values reduce
  to one, using the same rule as the hero terrain in ARCHITECTURE. Rows
  it cannot cover render as they do today.
- **Route to the scraper** (`core.events` should carry them) if coverage
  is poor. Quote the counts inline in its `docs/IDEAS.md`.

Name the choice and the coverage number.

## Acceptance

1. Profile rows show location and terrain wherever the chosen source has
   them. Check a past row and an upcoming row, named.
2. A row with no source renders as today (no empty badge).
3. Verified signed-in on own and someone else's profile.
4. Changelog entry.

## Out of scope

- Writing `core.*`.
- W-019's link logic.

## Premise corrected at review (2026-10-25)

`berlin_marathon` is back in the MV (one edition, 4 attendance rows), so
"Berlin has left it" no longer holds. For location the developer used the
tile's rule (earliest-dated race), not the hero's. The reason is in the
changelog, and the PM accepts it.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-044** — 2026-10-25. Rendered from
the worktree (`/proc/<pid>/cwd` → `irw-W027`), signed in on own `/profile/13`
and someone else's `/profile/15`, anon placeholder unchanged. Past row
(Spartathlon, no location) and upcoming row (Transgrancanaria) named. This
is web's first direct read of `core.mv_denormalized_event_data`. The
scraper's grant replay covers only the view, but production connects as
`postgres` (Paulo, 2026-10-25), so it has no grant gap. W-044 carries the
contract drift that remains. Ticket is `deploy: batched`.

**Not verified:** the grant path. Dev and prod both run as the owner, so a
non-owner role was never tried. The `other` terrain never won a row; it
gets the base neutral pill, the same one "Mixed" renders with today, so it
is not a defect. A row whose event is entirely absent from the MV: 46/46
found one, so the no-source path ran for location (Spartathlon) and never
for terrain. An event with two editions in the MV: none today, so the
"attended edition first, else earliest" ordering across editions has never
picked between two.
