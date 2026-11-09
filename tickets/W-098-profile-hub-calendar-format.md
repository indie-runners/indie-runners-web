# W-098 — The profile's race list uses the crew hub's calendar format

`priority: 2` · `effort: M` · `area: profile` · `deploy: immediate`
AMENDED 2026-11-04 (triage): part of the crews arc on Paulo's word (IDEAS 2026-11-04), so p2 and `deploy: immediate`, as PLAN's standing rule sets for every crews ticket.
`source: docs/IDEAS.md 2026-11-02 (Paulo)`

## What is wrong

Paulo, 2026-11-02: "the crew hub has a race calendar format. This format
should be the same within the user's profile."

## Evidence

The two formats today:

| | Crew hub (`crews_detail.html:51-90`) | Profile (`profile.html:7-38`) |
|---|---|---|
| Grouping | `<h2 class="crew-month">` per month, `%B %Y` | none, one flat list |
| Date block | left, day + weekday (`%-d`, `%a`) | right, day + `%b %Y` |
| Sub-line | location · distances in km | location only |
| TBC | under its expected month (December if unknown) | last |
| Marker | member chips | Going / Interested / Been there flag, terrain badge |

The hub's grouping is `CrewService.list_agenda`'s `month_of`
(`crew_service.py:183`), which reads `o.expected_month`. `ProfileRow`
carries neither `expected_month` nor distances.

## Acceptance

1. Both profile lists ("Race calendar" and "Been there") group under
   month headings and use the hub's left date block, day + weekday.
2. The sub-line reads location · distances, as on the hub.
3. TBC rows sit under their expected month, as on the hub.
4. **Defaults, veto at review:** the row keeps its Going / Interested /
   Been there flag and terrain badge (the hub's chips name members, a
   profile has one person). "Been there" stays a separate section,
   most recent month first (ARCHITECTURE:252 says why it is separate).
5. The calendar's empty state keeps the box W-101 gives it.
6. Verified signed-in on your own profile and on another member's.
   Anon: the profile redirect is unchanged.

## Out of scope

- The hub itself. Sharing one macro between the two pages is allowed,
  not required.
- W-084 (a running multi-day edition filed as past). Different bug,
  same service.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-084, W-073** — 2026-11-04.
Reviewed `fix/profile-hub-calendar-format` at `2528855`. Ticket is
`deploy: immediate`; this closes the crews arc's order table.

All six acceptance lines hold. The defaults stand: the flag and terrain
badge stay, and "Been there" stays its own section. Read on the branch:
the profile's month rule, its in-month order and its distance fallback
match `CrewService.list_agenda` line for line. That covers the date's
month, a TBC edition under its expected month or December, dated rows
by date with TBC last, and the attended edition's MV rows, else the
event's. The empty-state box from W-101 is untouched. The deleted grid
classes have no other user, and the hub's classes the row now borrows
are unscoped.

The one decision beyond the format is `COALESCE(a.race_date,
o.start_date)`. It is in scope: acceptance 3 says "as on the hub", and
five NULL snapshots have since gained a date that the hub already shows.
The changelog names it and its edge, none today.

The edge it leaves is the follow-up. Dated snapshots are still read as
taken, while the hub reads live dates. So the two pages can disagree on
a rescheduled edition, and nobody counted those rows. That is W-084's
shape, so **W-084 is amended** rather than a new ticket: measure first,
then read live dates for the row too. **W-073 is amended** to name the
distances fallback in ARCHITECTURE's ProfileService paragraph.

Verified from the worktree (`/proc/<pid>/cwd` → `irw-W098`), signed in as
user 13 on four profiles, captured against master first. Each section
holds the same (name, flag) set before and after, and anon renders
unchanged apart from the stylesheet hash.

**Not verified:**
- A real phone. Headless Chrome at 375px and 1280px only.
- A NULL snapshot whose edition has since dated into the past. It would
  move to "Been there", or vanish if it was Interested. None exists
  today, so that branch has never rendered.
- The "Date TBC" heading for a row with no occurrence year. Unreachable
  today: every attendance row has an occurrence.
- Routed check 51 watches the changed profile query in production.
