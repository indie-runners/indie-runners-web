# W-096 — Tiles lose the Going / Interested controls; the event page is the only place to mark a race

`priority: 2` · `effort: S` · `area: templates` · `deploy: immediate`
AMENDED 2026-11-04 (triage): part of the crews arc on Paulo's word (IDEAS 2026-11-04), so p2 and `deploy: immediate`, as PLAN's standing rule sets for every crews ticket.
`source: docs/IDEAS.md 2026-11-02 (Paulo)`

## What is wrong

Paulo, 2026-11-02:

> event pages should be the only place where the user is able to sign in
> to the race. Please remove the options from tiles. Tiles should still
> keep the sign-up button when the user is not yet logged in.

## Evidence

`app/templates/partials/race_tile.html`, the hover panel:

```
93   <a href="/auth/google" class="hover-cta">Sign in to join →</a>          (anon: keep)
97   {% if race.user_status == 'going' %}You are going{% else %}You are interested{% endif %}
101  <button class="attendance-change" ... >Change</button>
103  <button class="attendance-remove" ... data-action="remove">Remove</button>
109  <button class="hover-cta hover-cta--going" ... data-action="going">Going</button>
110  <button class="hover-cta hover-cta--interested" ... data-action="interested">Interested</button>
```

`static/js/attendance.js:111-131` rebuilds the same tile markup after a
click. It is shared with `event.html`.

## Acceptance

1. Signed in, no tile has a Going, Interested, Change or Remove button.
2. **Paulo confirmed 2026-11-03:** the read-only "You are going" / "You are
   interested" line stays on a tile the viewer has marked. It is a
   status, not an option.
3. Anon, the tile still shows "Sign in to join →".
4. The event page's controls still mark, change and remove, signed in.
   This must be re-run: the script is shared.
5. Counts and avatar strips on tiles are unchanged.

## Out of scope

- The attendance endpoints and the event page's own controls.
- Rewriting `attendance.js` beyond removing the tile-only branch, if it
  has one. If the branch is entangled, leave it and note it in DEV_NOTES.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-106** — 2026-11-04. Reviewed
`fix/tiles-drop-attendance-controls` at `14c950c`. Ticket is
`deploy: immediate`.

The script change is bigger than the spec expected: about 130 lines of
`attendance.js` go. It stays inside "removing the tile-only branch",
because each removed function only ever ran for a tile. Read on the
branch: the old updater scoped every query to the clicked container, and
on the event page that container is the action bar, which holds no
count, strip or hover face (`event.html:81-103`). So those lines were
no-ops there. Only `event.html` carries `data-action`. The script loads
from `base.html` on every page, so the mobile reveal handler still runs
on the index. Without the dropped exemption, an event-page tap passes
through it as a no-op, since there is no tile there. The file parses,
and nothing calls a removed function.

Verified from the worktree (`/proc/<pid>/cwd` → `irw-W096`): branch
against master side by side on the index, anon and two signed-in users.
The only differences are the controls. The event page was clicked
through Going, Change and Remove in headless Chrome, and the test user
ended with no attendance rows. The changelog cites the hover-panel entry
(IDEAS 2026-11-04) as a cost and claims no fix, which is right: the anon
"Sign in to join →" still sits in that last slot.

Follow-ups: **W-106**, the tile's unread calendar link. **W-062
amended** with the second false sentence the developer found. Both
DEV_NOTES entries get their annotation at the next triage, to keep
master's copy of the file clear of the branch's lines until merge.

**Not verified:**
- A real phone's tap-to-reveal on the index. Settled by Paulo tapping a
  tile twice after deploy: the first tap reveals, the second opens the
  event.
- A browser tab left open on the old index across the deploy. Its
  buttons still post to the unchanged routes and work. Routed check 50
  separates those from the old code still serving.
