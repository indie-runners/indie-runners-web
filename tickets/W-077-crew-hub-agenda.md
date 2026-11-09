# W-077 — The crew page shows who is in the crew, not where they are running

`priority: 2` · `effort: M` · `area: services` · `deploy: immediate`
`source: docs/IDEAS.md 2026-10-31 (Crews v1 spec, build step 2: hub agenda)`

**Crews arc, step 1. After W-076 is merged.** See `docs/PLAN.md`.

## What is wrong

`/crews/{slug}` has two sections, Members and Invite link. Paulo's outcome
for v1: *"A runner who joins a crew can see, in under a minute, which races
the crew is converging on over the coming months."* Nothing on the page
shows a race.

## Evidence

Spec, IDEAS 2026-10-31, § Hub page (quoted in full there): two columns,
agenda left, sidebar right, stacking on narrow screens; header "crew name,
label 'Crew hub'"; toggle "Going only" / "Going and interested", default
both; races grouped by month ascending from today; chips solid for going,
dashed for interested; *"Only occurrences that at least one member has
marked appear. Past occurrences do not appear."*

Paulo's decision 3: *"TBC still have a month and edition year. Go with a."*
That is: TBC editions sit under their expected month with a TBC date
block. The analyst counted 5 of 27 live non-past attendance rows as `tbc`.

What the spec assumes and the schema doesn't have:

- `web.attendance` is per **occurrence**, with no `race_id`. A row is an
  edition of an event, so "race name … location, distance" means event
  name, `event_location()` (W-070's rule, `race_service.py:87`) and the
  edition's list of distances.
- No htmx in `app/templates` or `static/`.
- `profile_service.py` already guards links with `has_page` (`EXISTS` on
  `core.v_denormalized_event_data_upcoming`, W-019). An edition that
  left the view has no page.

## Acceptance

1. One read over members ⋈ `web.attendance` ⋈ occurrences, plus one batched MV read for location and distances (the shape `ProfileService` already uses). The spec's "one statement" can't hold location from the schema alone. Grouped by month in Python. Non-past is the index's rule (W-020, `race_service.py:186-222`): a dated edition by its date, a TBC edition by the first of its expected month (December if NULL) against the current month. Not the profile's `is_upcoming`, which keeps a TBC whose month has passed.
   *Amended at review (2026-10-31):* a dated edition is non-past while `not is_locked(start, end)` (W-072), not by the index's per-race `race_date >= yesterday`: W-079 puts an attendance control on every row, and a locked row would refuse it. TBC keeps the index's month rule. Edition-level, the hub drops a dated edition one day before the index does.
2. Each row: date block (day number and weekday, or "TBC" under the expected month), event name linking to its page only when `has_page`, location by `event_location()`, distances, and one chip per member who marked it.
3. Chips go through `_is_identity_visible`, the predicate the event page uses. After W-076 every crew-mate passes it. It still matters if the hub deploys before 014 has run.
4. `?view=going` (or similar, no JS) hides rows with no going member and hides the interested chips. Default shows both.
5. The existing Members and Invite sections become the sidebar, unchanged in content. On narrow screens it stacks below the agenda.
6. Empty state: a crew with no marks says so and links to the index.
7. Verified signed in, at desktop and 375px: a crew with dated and TBC marks, the going-only toggle, an edition without a page (rendered unlinked), and the empty state. A non-member still gets `crews_hidden.html`. Anon still redirects to sign-in.
   *Amended at review (2026-10-31):* disproved — anon gets a bare 401 from `get_required_user`, on master too (DEV_NOTES 2026-10-31). Pre-existing, so not this ticket's: W-085.

If a CSS edit doesn't show locally, restart `dev.sh`: `static_url` caches its hash per process (DEV_NOTES 2026-10-30).

## Out of scope

- The attendance control on rows (W-079), "Next:" in Members (W-080), leave (W-081).
- The "next up" hero (artboard B) and the matrix view (artboard C).
- A second edition in the same year (EcoTrail Paris): `core.*`, raw on the scraper side.
- The Claude Design canvas: it can't be read from here, so the prose spec is the spec.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-085** — 2026-10-31. One ticket.
Changelog 1.9.51 names the wrong belief, the cost, the new belief and the
evidence, and states the one place the developer read the spec differently
(non-past as `is_locked`), with the reason; I accept it and amended
acceptance 1 to match. Chips pass through `_is_identity_visible` with
`{crew_id}` for both sets, which is exact here: the route checks membership
before `list_agenda`, and every attendee row comes from a membership join on
that crew. `has_page` is the profile's `EXISTS`, character for character;
the MV read is the profile's shape. Docs 55/100. No version constant in
code to bump. `deploy: immediate` (crews arc).

Render: the developer's default-view screenshots (their scratchpad,
`hub_1280.png`, `hub_375.png`) show the toggle as a dark slab with "Going
only" unreadable; their going-only shot is correct. I re-fetched the
default view from their `:8000` (both pids' cwd `irw-W077`, so the branch,
not master) as user 12 and screenshotted it at 1280 and 375 in a fresh
Chrome profile: the toggle renders correctly, and `main.css?v=a46b1068` is
the md5 of the committed file. The bad shots are from a stale stylesheet in
the screenshot run, cause not established; the committed state is right.

W-085: anon `GET /crews/{slug}` is a bare 401, and ARCHITECTURE § Crews,
in the paragraph this branch extended, still says an unauthenticated
visitor "bounces to Google". Pre-existing, found by the developer, filed.

**Not verified:** an edition without a page — `has_page` was true on all 8
live rows. That is also the path where location *and distances* fall back
to the event's other editions (`... or ev`), so the changelog's "that
edition's distinct distances" does not hold there; a degraded line on a
path with zero rows today, not ticketed. The empty state through the real
route (rendered through Jinja with `agenda=[]` only; a crew whose marks
are all past would reach it, and its `ANY(CAST([] ...))` read is the
profile's, which runs for every user with no marks). Going-only at desktop
width (seen at 375 only). A multi-day edition under a past month header
(Transgrancanaria in March) is read from the code, not seen. Copy on the
invite still binds by id after the `<aside>` wrap (`crews.js`), not clicked.

