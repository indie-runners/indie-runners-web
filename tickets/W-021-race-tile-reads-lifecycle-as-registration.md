# W-021 — `race_tile.html` reads a lifecycle column as registration status

`priority: 4` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-09-09 "FROM THE SCRAPER", part 2 (quoted below)`

## What is wrong

`app/templates/partials/race_tile.html:5`:

```jinja
{% set reg_open = race.race_status and 'open' in race.race_status | lower %}
```

`race_status` is `core.races.status`. From the scraper's note:

> **`race_status` is `core.races.status`, whose vocabulary is `active |
> inactive | cancelled`** — it says whether a race exists and is served,
> not whether registration is open. `'open'` is not a substring of any of
> those, so `reg_open` has never once been true … **Registration status
> lives in the answers, not in `core.races.status`** — `registration_open`
> is a question column on the same view.

So the "registration open" branch is dead code today, and it is armed:
any future status value containing `open` lights a false badge on every
tile of that race. `registration_open` is already mapped
(`app/models/core.py:63`, `Boolean`) but is not carried into
`EventListItem`.

## Acceptance

1. `reg_open` no longer reads `race_status`. The developer chooses between
   (a) wiring `registration_open` through and (b) deleting the dead
   branch, **names the choice and why**, and checks the render either way.
2. If (a): `registration_open` is race-level and the tile is event-level,
   so state the ANY-of-races rule, the same convention as formats.
   `NULL` means unknown, not closed.
3. Verified in the browser, anon and signed-in.
4. Changelog entry.

## Out of scope

- The scraper's constraint never to introduce an `open`-containing
  status value. It is theirs, and it is the reason this is p4.
- Any other use of `race_status`.

## Verdict

**VERDICT: APPROVED** — 2026-10-27. Choice (a), wire-through, named and
argued from coverage. ANY-of-races stated, NULL kept as unknown. Verified
from the worktree on :8001 (cwd checked, so not W-009), anon and signed-in:
60/60 tiles agree with `bool_or(registration_open)`, 37 badged. Master shows
0. Ticket is `deploy: batched`.

**The open TODO question (anon sees the badge): yes, that is fine. Decided
here, no follow-up.** The tile already shows price and distances to anon
users. The original badge had no gate either. The `event.html` gate is
about the race table on that page, as ARCHITECTURE § Signed-out UX states
it, not a site-wide rule that registration is for signed-in users. Paulo
can overrule; it would be a one-line `current_user` gate.

**Not verified:**
- A TBC tile with an open race. The `not race.is_tbc` guard is unchanged,
  but nothing shows such a tile rendered. Settles: one anon `/` render
  where a TBC event's `bool_or` is true.
- Filtered lists. `?search=` filters race rows in SQL, so ANY covers only
  the matched races. Formats and distances already behave this way.
  Only `/?country=fr` was run, which filters event by event and cannot
  split one.
- Events past the 60-tile cut, except as filters surface them.
