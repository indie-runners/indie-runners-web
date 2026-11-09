# W-070 — One rule for an event's location: HQ, else the first race with a start town

`priority: 3` · `effort: S` · `area: services` · `deploy: batched`
`source: Paulo, triage 2026-10-28, revising his 2026-10-27 ruling in docs/DEV_NOTES.md (while on W-013)`
`supersedes: W-055, W-069`

## What is wrong

Four places show an event's location, each by its own rule:

| Where | Reads | Today |
|---|---|---|
| event hero (`main.py:403`, `event.html:42`) | `event_location` | empty on all 396 events |
| home tile (`race_service.py:242`) | first-see race's `race_location`, NULL or not | "—" when that race has no town (`otf_presented_by`) |
| calendar link (`main.py:419`, `race_tile.html:7`) | `event_location` / tile location | as above |
| profile calendar (`profile_service.py:173-177`) | earliest-dated race with a town, from the MV | a town |

So Transgrancanaria is "—" or "Artenara" depending on the page, and no
hero shows a town at all.

## The rule (Paulo, 2026-10-28)

> is there an event headquarter? if yes, then display it. if not, is
> there a race start location for the first race? if yes, then display
> it, if not, is there a race start location for any race? if yes,
> display it, if not, the empty.

Steps 2 and 3 are one step: the first race, in first-see order (date,
then `mv_id`, W-029), that has a `race_location`. So:
**`event_location`, else first race with a town, else empty.**

This replaces the 2026-10-27 ruling "don't fall back to a race town".
Step 1 returns empty until the scraper populates `event_location`
(routed 2026-10-28, their T-039). The day it does, every page shows
HQs with no web change. That is the point of coding step 1 now.

## Acceptance

1. **Measure first, read-only, one session.** Events where the first-see
   row's `race_location` is NULL and a sibling has one (W-055's count),
   and events with no town on any race. Quote both and the query in the
   changelog.
2. One shared function holds the cascade. Tile, hero, calendar link and
   profile calendar call it; no page keeps its own location read. The
   profile passes the attended edition's rows where the MV still holds
   them (its current rule), so "agree" means same edition, same town.
3. `otf_presented_by`'s tile shows the town the profile shows. The
   Athens hero reads `Athens · Greece · 7 November` (after W-065).
   An event with no town anywhere shows "—" on the tile and no location
   item in the hero. Quote all three renders, anon and signed in.
4. ARCHITECTURE:70-86 states the cascade once, replacing "though the
   profile skips a NULL `race_location` and the tile does not", and
   says the hero shows a race start until `event_location` is populated.

## Out of scope

- **Terrain.** Tile first-see vs profile longest-race, by design (W-027).
- **Filters changing the first race** (`search`, dates). W-029 named
  it; the tile's town can still change under a search.
- The meta-row separators and country casing: W-065, which goes first.
- Any guess at an HQ on the web side (deriving it, hand lists). The
  scraper produces `event_location`.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-073** — 2026-10-30. The changelog
names the wrong belief (each page could pick its own town), its cost
(`otf_presented_by` "—" on the tile, Oberaudorf on the profile; no hero
town), the new rule and the measurement that came first (4 first-see-NULL
events, 10 with no town, 0 `event_location`). One function,
`event_location(rows)`, sorts its own input, so the hero's distance order
and the tile's date order give the same town. The profile's
`mv_id::text` sorts like the ORM's UUID string, so its tie-break matches
the tile's. Grep finds no other event-level location read; `event.html:240-261`
is the selected race's own `race_location`, as it should be. The worktree
was served from its own checkout (`/proc/<pid>/cwd`, so W-009 doesn't
apply), and both tiers were rendered: the signed-in tier from a minted
cookie, so this checks the render, not sign-in. The developer flagged the
one place the spec changed the profile's behaviour (stop at the attended
edition) and measured it at 0 of 52. Docs: 73 lines. `deploy: batched`.

W-073: ARCHITECTURE:81-82 says all ten no-town events show "—" on the
tile. 8 are TBC, and a TBC tile has no Location row (`race_tile.html:51-54`).
The changelog has this right.

**Not verified:** step 1. No row carries `event_location`, so the HQ
branch has never run. It settles when the scraper's T-039 lands and a hero
shows a town that is not any of its races' `race_location`. Also not run:
a profile row whose attended edition has MV rows but no town while another
edition has one (0 of 52). The new rule shows nothing there, where the old
SQL fell through to the other edition. And `biegi_gorskie_sanok`,
`kielder_marathon` and `walt_disney_world` were counted, not rendered.
They take the same path as `otf_presented_by`. Routed as check 33.
