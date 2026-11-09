# W-040 — A finished edition's URL answers raw JSON 404, even when the next edition has a page

`priority: 2` · `effort: S` · `area: routing` · `deploy: batched`
`source: AUDIT_20261023T1719 F1; mechanism confirmed by the PM 2026-10-24`

## What is wrong

`event_detail` (`app/main.py:339-357`, master) looks up exactly
`(event_slug, occurrence_year)` in the serving view and raises
`HTTPException(404)` if no row matches. The view drops a non-TBC race the
day after it runs (W-012), so every finished edition's URL dies. What the
person gets is FastAPI's default JSON. A bookmark, an old tab or a search
result shows `{"detail":"Event not found"}`. That is the same defect W-035
fixed for `/settings`.

The next edition usually exists. Every dead URL from the audit sample has
a live page one year on.

## Evidence

Audit, 24h of `GET 404` (AhrefsBot, SemrushBot, bingbot unless noted):

```
17:20 /events/grand_trail_templiers/2026   (Chrome/146)
17:02 /events/kustmarathon_zeeland/2026    (Chrome, referer https://indierunners.co)
17:00 /events/budapest_half_marathon/2026  (Chrome)
14:31 /events/paris_versailles/2026   13:56 /events/odyssea_paris/2026   11:25 /events/ecotrail_paris/2026 ...
```

PM, 2026-10-24, serving `00059-z4t`:

```
$ curl -s -i https://indierunners.co/events/grand_trail_templiers/2026
HTTP/2 404
content-type: application/json
{"detail":"Event not found"}

grand_trail_templiers/2027 200   kustmarathon_zeeland/2027 200
budapest_half_marathon/2027 200  paris_versailles/2027 200   ecotrail_paris/2027 200
```

The site itself doesn't mint these links. None of the six slugs appears
with any year in the HTML of `/` or `/stats`, and profiles link only
editions that have a page (routed check 3). The traffic comes from
outside: crawler memory, bookmarks, search results.

## Acceptance

1. `GET /events/<slug>/<year>` with no row for that year, but a row for
   the same slug in the view, redirects to that slug's edition. The
   developer names which edition (nearest upcoming, presumably), the
   status code (301 or 302) and why. A 301 is cached by browsers, and
   with D+2 retention (W-012) the old year can come back for two days.
2. With no row for the slug at all, the response is an HTML page a
   person can read, with a link to `/`, still status 404. It is not JSON.
3. `HEAD` answers like `GET` on both paths (routed check 1's rule).
4. Quoted curl output for `grand_trail_templiers/2026` (redirect), a
   made-up slug (HTML 404) and a live edition (unchanged 200), anon and
   signed in.
5. The changelog names the trade-off in 1: a redirect makes an old URL
   answer for an edition the person did not ask for.

## Out of scope

- Retention. W-012 and scraper T-134 keep an edition for two more days.
  That postpones the 404, it doesn't remove it.
- Other `HTTPException` 404s (`/crews/{slug}`, the join POST). They may
  share the JSON body, but this ticket is the route the audit measured.
  If the fix is a shared HTML error handler, say so in the changelog and
  check that JSON callers (`/events/.../attendance`) still get JSON.
- `robots.txt` and `sitemap.xml` (W-006, W-010).

## Verdict

**VERDICT: APPROVED** — 2026-10-24. All five acceptance items met: 302
to the first edition after the year asked, else the latest; 302 over
301 argued (yearly target, D+2 can bring the year back); route-local
HTML 404 for an unknown slug; trade-off and the dropped `?race=` named.
No redirect loop: the target year comes from the same view and slug
predicate the route matches on, so it always has rows. The Location is
built only from a slug the view holds. Verified on `:8040` with
`/proc/<pid>/cwd` → `irw-W040`, GET and HEAD, anon and signed in, all
six audit slugs. Ticket is `deploy: batched`. Routed check 14.

**Not verified:** the 404 page was checked by curl body text, never
seen in a browser (classes are reused from `crews_hidden.html`, so low
risk). A slug whose newer rows are a stale past-dated TBC edition
(W-012's amendment) would redirect to that TBC page; nobody ran one.
The D+1/D+2 window after scraper T-134 ships (`/2026` answers 200 for
two days, then 302) cannot run until then.
