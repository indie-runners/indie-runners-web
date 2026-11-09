# W-073 — ARCHITECTURE says a no-town event shows "—" on its tile; 8 of 10 are TBC and show no Location row

`priority: 5` · `effort: S` · `area: docs` · `deploy: batched`
`source: W-070 review, 2026-10-30`

## What is wrong

`docs/ARCHITECTURE.md:81-82` (as merged by W-070, 1.9.46):

> and ten had no town on any race — those show "—" on the tile
> and no location item in the hero.

W-070's own changelog says 8 of those 10 are TBC, and
`race_tile.html:51-54` renders the TBC notice *instead of* the Location
row: "`berlin_easter_run` (TBC) … its tile has no Location row, as every
TBC tile." The sentence is true for `borsig_half_marathon` and
`hunsbuckel_trail` only. Changelog and ARCHITECTURE disagree on the same
branch.

Same paragraph family, same shape: the ProfileService paragraph
(ARCHITECTURE:251) now says location stops at the attended edition's MV
rows when it has any, while terrain's subquery still orders the attended
edition first and **falls through** to other editions when it has rows
but no terrain. The paragraph doesn't say the two differ.

## Acceptance

1. :81-82 says a non-TBC event with no town shows "—" on the tile; a TBC
   tile has no Location row at all.
2. The ProfileService paragraph names the asymmetry in one clause:
   location stops at the attended edition when the MV holds it, terrain
   falls through.
3. Docs only.

## Out of scope

Changing either rule. Terrain's rule is W-027's and out of W-070's scope.

AMENDED 2026-11-04 at the W-098 review. Since 1.9.67 the profile row
also carries distances, from the same MV rows as location: the attended
edition's, else every MV row of the event (`profile_service.py`
`_edition`, the hub's rule in `crew_service.py`). ARCHITECTURE's
ProfileService paragraph still says only "Location and terrain come
from the MV". Name distances there, with the same fallback and the
assumption it carries: a series keeps its distances.
