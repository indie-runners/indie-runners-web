# W-062 — ARCHITECTURE names an action-bar avatar strip that isn't there

`priority: 5` · `effort: S` · `area: docs` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-27 (while on W-028), filed at the W-028 review`

## What is wrong

`docs/ARCHITECTURE.md:183`, § Who's coming:

> the action bar continues to trim display via the shared `avatar_strip`
> macro's `cap` argument

The developer's drive-by (DEV_NOTES 2026-10-27): "`avatar_strip` is
called only from `race_tile.html` and the anonymous who's-coming row
(`event.html:508,516`); the event page has no action-bar strip." The
paragraph above it already says the action-bar strips "were removed as
duplicates of the Who's coming section below". The document contradicts
itself.

## Acceptance

1. :183 names the macro's real callers, or drops the action-bar clause.
2. `git grep -n "avatar_strip(" app/` matches what the paragraph says.
3. Docs only.

## Out of scope

The rest of ARCHITECTURE's staleness (W-036, W-038, W-044 each own one).

AMENDED 2026-11-04 at the W-096 review. The same paragraph, `:187` after
W-096, has a second false sentence:

> Clicking Going / Interested from the action bar continues to update the
> strip and counts via `attendance.js`

The action bar has no strip and no counts, so the script never updated
either on the event page. Acceptance 1 covers this sentence too: drop it,
or say the script rebuilds only the bar's status and buttons.
