# W-108 — The tile panel's +N fitting misfires when a row other than the pills overflows

`priority: 2` · `effort: S` · `area: templates` · `deploy: batched`
`source: W-107 review 2026-11-04 (DEV_NOTES 2026-11-04, while on W-107)`

## What is wrong

W-107's `fitDistances` (`static/js/attendance.js`) assumes the pills are
what overflow `.hover-rows`. It appends the +N pill before it knows that
hiding a pill helps, then hides pills from the end until the rows fit or
one pill is left. When something else overflows, such as a location that
wraps, two things go wrong:

1. **One pill:** the loop never runs. An empty, bordered `+N` pill stays
   in the panel. Every non-TBC tile has at least one pill (the `—` fallback).
2. **Two or more pills:** the distances collapse to one pill and `+N`.
   The rows still overflow, and the clipped row has no visible sign.
   That breaks W-107 acceptance 3: nothing is trimmed without a sign.

## Evidence

From W-107's changelog 1.9.68, and the `shortcut:` at `.hover-rows`:

> Gapa Everesting Festival, signed out at 1101 to about 1129px:
> "Garmisch-Partenkirchen" wraps and the entry fee row is cut by 14px.
> One tile of 456

Production, `/?search=gapa`, 2026-11-04: two pills, `19.8 km` and
`59.4 km`, so case 2 applies to Gapa today. No single-pill tile overflowed in
W-107's 456-tile sweep, so case 1 has never rendered.

## Acceptance

1. The +N pill appears only when hiding pills made the rows fit, and
   never empty.
2. If hiding pills does not help, every pill shows. Whatever is still cut
   either has a visible sign or no longer happens. Gapa at 1101 to 1129px,
   signed out, is the test tile.
3. Re-run W-107's sweep: anon at 1101, 900 and 650px over the month
   filters. The last line stays inside every tile.

## Out of scope

- Ranking or dropping rows. That remains Paulo's call (W-107).
- The breakpoints and the faces, both settled in W-107.
- The dead `avatar_strip` size argument, `.avatar--lg` and `.hover-avatar`
  (DEV_NOTES 2026-11-04). They are not this defect and go to triage.

## Verdict

**VERDICT: BLOCKED — R1** — 2026-11-04. Reviewed `6e44976`. The code passes.
The `fitDistances` revert meets acceptance 1 and 2, and both forced-overflow
cases were run. The sweep was served from the worktree, checked by `/proc` cwd.
It covered both tiers. The idle panel is `opacity: 0`, not `display: none`, so
measuring it unhovered measures real layout. Docs: 44 lines, version bumped,
no ARCHITECTURE or FILE_TREE change needed.

**R1 — the headline and the deleted `shortcut:` claim more than the sweep
shows.** "Keeps its pills and its entry fee at the narrowest widths" is
stated universally. `.hover-rows` still clips with `overflow: hidden` and no
sign. The 1101 to 1130px spacing was tuned until today's 457 tiles fit. The
changelog's own figures put the margin near the width of the cut: San
Sebastian was cut 21px and the band takes back about 22px. A longer name, or
the badge plus both attendee blocks, cuts the entry fee silently again. The old
`shortcut:` named "a row that wraps", and that cause is gone. The limit itself
remains: the fixed blocks still squeeze the rows with no sign. The next
developer inherits a comment that reads as settled. **Unblocks it, prose only,
no code:**
1. A `shortcut:` at `.hover-rows` naming the real limit and the margin left
   on the tightest tile at 1101px.
2. The same in `docs/DEV_NOTES.md`, replacing the W-107 note, which still
   reads live.
3. Scope the changelog headline and new belief to the corpus that was swept.

**Not verified:**
- Tiles that do not exist yet at 1101 to 1130px: three-line names, the badge
  plus both attendee blocks. Settled only by a sweep after the corpus changes.
- Font metrics outside Chrome at that band, with the margin above.
- Signed in over the month filters, at any width but 1101px.
- A real pointer hover. The panel was revealed by class.
- Touch: the town's `title` cannot be seen. The event page has the full name.

Routed check 53 is written with the approval. It covers Gapa and San
Sebastian at 1101 and 1110px signed out, and it ends check 52's Gapa exemption.

### Re-review

**VERDICT: APPROVED** — 2026-11-04. Reviewed `8c859e7`. R1 resolved. The
headline is scoped to the swept tiles. The `shortcut:` at `.hover-rows` names
the limit and the margins measured at 1101px, and DEV_NOTES replaces the W-107
note. No code changed since `6e44976`. Docs 59 lines. Ticket is
`deploy: batched`. Routed check 53.

**Not verified:**
- The 0.4px overhang on three of the four tiles: Val Daran Pyrenees, Bucovina
  Ultra Rocks and Gletscher Trailrun. Only Stuiben Trailrun's screenshot was
  checked by eye. One screenshot each at 1101px, signed out, would settle it.
- The earlier list still stands: unswept tiles, other browsers' fonts,
  signed in away from 1101px, a real pointer hover, and touch.
