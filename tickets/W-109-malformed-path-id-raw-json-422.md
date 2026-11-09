# W-109 — A profile or event URL with a malformed number answers raw JSON 422

`priority: 2` · `effort: S` · `area: routes` · `deploy: batched`
`source: AUDIT_20261105T0851 F3; reproduced by the PM 2026-11-05`

## What is wrong

Two page routes type a path segment as `int`: `user_id` on
`GET /profile/{user_id}` and `occurrence_year` on
`GET /events/{event_slug}/{occurrence_year}`. A segment that is not a bare
integer (a pasted link with a trailing `+`, a typo) fails FastAPI's
validation before the route runs, and the visitor gets the framework's
JSON body instead of a page. Same class as W-035 (raw 401), W-040 (raw
404) and W-092 (raw 422), on two routes they did not cover.

## Evidence

Production request log, from the audit:

```
2026-11-04T13:40:18.839Z  00087-q68  GET 422  https://indierunners.co/profile/27+  Firefox/158.0 (Ubuntu), no Referer
```

Reproduced against `00092-vzb`, 2026-11-05:

```
/profile/27+                        422 application/json {"detail":[{"type":"int_parsing","loc":["path","user_id"],...
/profile/abc                        422 application/json {"detail":[{"type":"int_parsing","loc":["path","user_id"],...
/events/tenerife_bluetrail/2027x    422 application/json {"detail":[{"type":"int_parsing","loc":["path","occurrence_year"],...
/events/tenerife_bluetrail/1999     302 text/html     (W-040's redirect: a well-formed year with no row)
/profile/999999                     200 text/html     "This runner keeps their profile private" (deliberate, no enumeration)
```

The index's filters are parsed leniently from strings (`_parse_filters`),
so `/` does not 422 on a bad filter. The two routes above are the class.

## Acceptance

1. `GET /profile/27+` and `GET /profile/abc` answer an HTML page, never
   JSON. The page is the one an unknown id already gets
   (`profile_hidden.html`), so a malformed id gives no signal an unknown
   one does not (ARCHITECTURE: no enumeration channel).
2. `GET /events/<slug>/2027x` answers HTML, never JSON: either W-040's
   path (redirect to the slug's edition) or `event_not_found.html` with a
   `404`. Developer's choice; say which in the changelog.
3. Well-formed URLs behave exactly as today: `/profile/<real id>`,
   `/profile/999999` (placeholder, `200`), `/events/<slug>/<year>`, and
   W-040's redirect for a year with no row.
4. Verified signed out and signed in, on all of the URLs above.

## Out of scope

- `POST /crews/{slug}/members/{user_id}/remove` and other POST routes with
  an `int` segment. A form posts them, not a pasted link.
- A global validation handler for every route, unless it is the smallest
  change that meets 1 to 3. The JSON API routes, if any, keep JSON.
- `/profile/999999` returning `200` rather than `404`. Deliberate.

## Why batched

One hit in 24h, a malformed link, no data at stake. No `immediate` ticket
is on deck, so under the batch rule it ships within 14 days of `done`.
