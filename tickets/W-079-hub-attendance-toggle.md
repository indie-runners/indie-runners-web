# W-079 — A crew member can't add themselves to the plan from the hub

`priority: 2` · `effort: S` · `area: services` · `deploy: immediate`
`source: docs/IDEAS.md 2026-10-31 (Crews v1 spec, build step 3)`

**Crews arc, step 3. After W-072 is merged and W-077 is merged.** The toggle wraps `mark_attendance` and `clear_attendance` as W-072 leaves them, past-date lock included.

## What is wrong

The hub (W-077) shows who marked a race, but the viewer has to open the
event page to mark it themselves.

## Evidence

Spec, § Attendance control on the hub:

> Two segment control per race row: [Going | Interested].
> - Clicking the other segment switches status.
> - Clicking the filled segment clears status.
>
> Backend rule: if the posted status equals the current status, delete the attendance row; otherwise upsert. Expose this as a toggle method on the attendance service so the race page could use the same logic later. The race page keeps its current "change / remove" pattern in this version.
>
> After the post, re-render the row (htmx partial if available, otherwise full page redirect back to the hub).

No htmx in the app, so: a form POST and a 303 back to the hub.

W-072 (branch `fix/past-attendance-lock`, in review at triage) changes both methods: *"lock attendance the day after an edition's last known day; both routes refuse"*.

## Acceptance

1. `AttendanceService.toggle(user_id, event_id, occurrence_id, status)`: same status → `clear_attendance`; otherwise → `mark_attendance`. No new date or validity rule; it inherits W-072's.
2. `POST /crews/{slug}/attendance`: member only (404 otherwise, as rotate does), then toggle, then 303 to the hub with the row's month anchored.
3. Each hub row shows the viewer's two segments, the filled one being their status. A locked edition (W-072's predicate) shows no control.
4. The event page's control is unchanged.
5. Verified signed in: none → going, going → interested, going → none (click the filled one), and a non-member POST is refused. The chip on the row follows each change.

## Out of scope

- Replacing the event page's change/remove control (an open decision in the spec).
- The Origin check on this POST: W-031 covers every attendance POST, and none of them is irreversible.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-089** — 2026-11-01. Ticket is
`deploy: immediate`.

The toggle is the spec's rule and adds nothing to it. A bad status never
equals the held one, so it falls to `mark_attendance`'s check. Both
branches go through W-072's lock. The route is member-gated like rotate.
`viewer_status` is set before the visibility filter, so the viewer always
sees their own mark. The changelog names the wrong belief, its cost, the
new belief and the evidence. It verified against this worktree's process,
not another checkout's (W-009). Docs: 48 lines. ARCHITECTURE is updated
and no file is added.

Acceptance 3 holds by argument plus one measurement, not by construction.
The argument is that `list_agenda` drops every locked dated row. The
measurement is that TBC rows with a past `start_date` number 0 among
attended rows today. The changelog says this honestly. ARCHITECTURE's
"every rendered row carries the segments" is true but invites the wrong
inference that every rendered row can be toggled. **W-089** owns the
gap. It also owns the refusal's render: on the hub a 400 is a navigation,
so the reader lands on FastAPI's JSON body, which the event page's script
hides.

Both tiers: anon never renders the hub, so anon is the POST's 401, which
was checked. The signed-in tier used a minted cookie and headless Chrome
at 1280 and 375 px.

At merge: master's triage commits changed W-079's notes, so the CSV
conflicts on that row. Keep master's notes with the branch's
status and branch. The branch also stripped the quotes from W-084's and
W-087's notes. The values are unchanged, but those columns are the PM's,
so keep master's bytes.

**Not verified:** a real Google sign-in; the `#m-YYYY-MM` fragment
landing in a real browser; a toggle on a TBC row (only a dated row was
exercised, though the code path is the same); a row that locks between
render and post; the landing after clearing the only mark on a row, which
should be the top of the page. Routed check 40 watches for the 400.
