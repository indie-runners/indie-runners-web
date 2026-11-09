# W-107 — On a crowded tile the hover panel's last line is cut off

`priority: 2` · `effort: S` · `area: templates` · `deploy: immediate`
`source: docs/IDEAS.md 2026-11-04 (Paulo); settles the 2026-10-30 mobile entry`

> **Amended at review, 2026-11-04.** The premise and acceptance 3 and 4
> changed mid-ticket on Paulo's word, and out of scope item 2 was lifted.
> See § Amended at review. The text above that section is the original spec.

## What is wrong

The tile has a fixed 3:4 shape and hides whatever overflows it. The
hover panel fills the tile and stacks everything in one column, with no
limit on how tall its content grows. When an event has many distances,
or both a going and an interested block, the content outgrows the tile.
The last line falls below the bottom edge and is clipped. For a
signed-out visitor that line is "Sign in to join →". For a marked tile
it is "You are going".

## Evidence

Paulo, from `docs/IDEAS.md`, 2026-11-04:

> the biggest problem with the tiles nowadays is that, where there are
> many races per event, or many people going/interested, then the
> buttons get hidden in the bottom, both on desktop and mobile.

Paulo, 2026-10-30, the same problem on mobile, left raw at the time:

> when the index tile is clicked on, while on mobile, the information on
> the race comes up, but often times it hides out because there is
> already a lot. What should we prioritize so that everything fits?

The mechanism, read from source and not yet seen in a browser:

```
static/css/main.css:313  .tile { position: relative; ... overflow: hidden; aspect-ratio: 3/4; ... }
static/css/main.css:422  .tile-hover { position: absolute; inset: 0; ... display: flex; flex-direction: column; ... }
static/css/main.css:538  .dist-pills { display: flex; flex-wrap: wrap; ... max-width: 65%; }
app/templates/partials/race_tile.html:55-64   one dist-pill per distance, wrapping
app/templates/partials/race_tile.html:78-91   a going block, then an interested block when interested_count > 0
app/templates/partials/race_tile.html:92-101  "Sign in to join →" (anon) or the status line (marked), last
```

The faces are already capped at three per block, so the distance pills
and a long event name are what grow.

## Acceptance

1. On every tile, the panel's last line is fully visible: "Sign in to
   join →" signed out, "You are going" or "You are interested" on a
   marked tile. Checked at each grid width (4, 3, 2 and 1 columns, the
   breakpoints at 1100, 780 and 480px) and at 375px, on hover and on
   the mobile tap-to-reveal.
2. The test tiles are named in the changelog: the event with the most
   distances, and one with both going and interested. Screenshot each,
   before and after.
3. Default, veto at review: the last line is pinned to the bottom and
   never clipped. When the distances do not fit, the panel shows as many
   pills as fit and a "+N" pill for the rest. Nothing is trimmed without
   a visible sign that there is more on the event page.
4. A tile with little content looks as it does today.
5. The sign-in link and the tile link still work on a revealed tile
   (first tap reveals, second tap opens the event).

## Out of scope

- Ranking or dropping fields (date, country, location, entry fee). That
  was the 2026-10-30 entry's open question. If the default in 3 is not
  enough, the developer stops and shows Paulo a screenshot.
- The tile's front face (`tile-base`) and the event page.
- W-106 (the tile's unread calendar link). It is a dead attribute, not
  layout, and stays its own ticket.

## Amended at review

Recorded from the branch's changelog 1.9.68 and TODO. Paulo's two
decisions are on the developer's word, made outside this repo.

- **The mechanism was wrong.** Measured on master, the last line fell
  off 58 of 60 anon tiles at 781px and 481px, not only crowded ones.
  The attendee faces, not the pills, took the height.
- **Acceptance 3 was not enough.** The +N default held the last line but
  squeezed rows to 0px at 481px. Paulo chose instead: no faces in the
  panel, counts stay, and the +N pill stays.
- **Acceptance 1's breakpoints moved.** 2 columns from 899px (was 780),
  1 column from 649px (was 480). Four columns are unchanged.
- **Acceptance 4 is relaxed.** A little-content tile changes too: its
  panel loses its faces.
- **Out of scope item 2 is lifted** for the grid widths only. The front
  face grows at 650 to 899px and below 650px. Paulo approved it.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-108** — 2026-11-04. Reviewed
`fix/tile-hover-panel-clips-bottom` at `035bca2`. Ticket is
`deploy: immediate`.

The changelog carries the reasoning to the standard: the wrong belief
(only crowded tiles, pills grow), its measured cost, the new belief (a
panel fits a tile about 260px wide), and the widths that separate them.
It is one ticket. The breakpoint move, the faces and +N all answer the
same clipping, and the scope change went to Paulo rather than around
him. Docs 58 of 100 added lines. ARCHITECTURE:183 is corrected, and no
file was added or removed. `.race-grid` exists only on the index, and no
other rule keys on 780 or 480px, so the breakpoint move reaches nothing
else. `.dist-pill` sets no `display`, so `hidden` works on it. The
verification ran from the worktree (`/proc` cwd checked), both tiers,
with hover and tap.

**The follow-up is a path the sweep could not see.** `fitDistances`
creates the +N pill before it knows hiding helps. On a tile with one
pill that overflows for another reason, it leaves an empty bordered
pill. When a wrapping row overflows, it collapses the distances to one
and still clips the row. Gapa Everesting Festival has two distances (production
`/?search=gapa`, 2026-11-04), so it shows "19.8 km +1" with the entry
fee cut. No single-pill tile overflowed in the 456-tile sweep, so the
empty pill has never rendered. One tile in a 28px window does not block
an immediate fix. W-108 covers both.

**Not verified:**
- A real phone or Safari. Headless Chrome with tap emulation only.
- The no-JS path. The changelog says rows clip with no +N. Nothing shows
  it was run, and acceptance 3's visible sign is absent there.
- Signed in over the month filters. Signed-in tiles were measured on
  the 60 tiles of `/` only, so a marked tile with many distances and an
  interested block may not have been in the set.
- The before and after screenshots went to Paulo. This review did not
  see them.
- Paulo's two decisions are recorded only in the changelog and TODO.
- Routed check 52 watches the served page and stylesheet.

