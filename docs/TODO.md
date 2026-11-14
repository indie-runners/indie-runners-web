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

- FastAPI's `int` accepted `+27` / `-1`; a strict ASCII-digit check sends
  those to the placeholder too. Neither has a row, so the page is the same.

## Disproved / found

- A strict ASCII-digit check was enough; no global handler needed.
- A 20-digit id still 500s (bigint out of range), as it did under `int`:
  Drive-by on the board, outside this ticket.
