# TODO: #14 — A profile or event URL with a malformed number answers raw JSON 422

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-14_

## Steps

- [x] `/profile/{user_id}` and `/events/{slug}/{occurrence_year}`: take the
      segment as `str`, parse it in the route; not a bare ASCII integer →
      the page an unknown value already gets
- [x] Profile: `profile_hidden.html`, 200 (same as an unknown id)
- [x] Event: `event_not_found.html`, 404
- [x] Changelog, version bump

## Measure, both tiers (anon and minted cookie)

- `/profile/27+`, `/profile/abc` → HTML placeholder, not JSON
- `/events/<slug>/2027x` → HTML 404, not JSON
- unchanged: `/profile/<real id>`, `/profile/999999` (placeholder 200),
  `/events/<slug>/<year>`, W-040 redirect for a year with no row

## Unsure

- FastAPI's `int` accepted `+27` / `-1` (pydantic, checked). The strict
  check sends them to the placeholder: same page for a profile, but
  `/events/<slug>/+2027` used to render the edition and `/-1` redirect;
  both are now 404. The site never links a signed year; told the PM.

## Disproved / found

- A strict ASCII-digit check was enough; no global handler needed.
- R1 (PM): `int()` refuses > 4300 digits, a 500 the unbounded check
  created. Capped at 18 digits, which also closes the bigint Drive-by.
