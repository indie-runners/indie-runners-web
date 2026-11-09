# W-006 — `/robots.txt` 404s, so authenticated surfaces are offered to crawlers

`priority: 3` · `effort: S` · `area: routing` · `deploy: batched`
`source: exports/reports/AUDIT_20260828T0812.md` (F3, first half)

## What is wrong

The site serves no `robots.txt`. A 404 there is read by crawlers as "crawl
everything", so `/settings`, `/profile/{user_id}`, `/crews/{slug}`,
`/crews/join/{token}` and `/auth/*` are offered for indexing alongside the
event pages.

The defect is not the missing file as such — it is that this site has **no
stated crawl policy** while deliberately courting crawlers. `docs/PLAN.md`
ticket 2 puts a `short_description` block *outside* the `{% if current_user %}`
gate specifically so it is crawlable, and adds a `<meta name="description">`.
Organic search is a goal of this product; the auditor flagged F3 without a
basis to judge that, and PLAN.md is the basis.

`/crews/join/{token}` is the one that is more than hygiene: an invite token in
a crawled URL is an invite token in a search index.

## Evidence

Live, at audit time:

```
/robots.txt -> 404
```

Real crawler traffic, three requests in 24h:

```
2026-08-28T03:17:19.576233Z	404	https://indierunners.co/robots.txt
2026-08-28T03:07:07.009909Z	404	https://indierunners.co/robots.txt
2026-08-28T02:41:48.089899Z	404	https://indierunners.co/robots.txt
```

No route and no static file exists — verified on `master`:
`grep -rn "robots" app/` returns nothing, and `/static` is mounted from
`_static_dir` (`app/main.py:83`) with no `robots.txt` in it.

The authenticated surfaces, from the route list in `app/main.py`:

```
494:@app.get("/profile")
499:@app.get("/profile/{user_id}")
569:@app.get("/settings")
637:@app.get("/crews/{slug}")
697:@app.get("/crews/join/{token}", name="crews_join_form")
796:@app.get("/auth/google")
```

## Acceptance

- `GET /robots.txt` returns **200** with `Content-Type: text/plain`.
- It disallows at minimum `/settings`, `/profile/`, `/crews/`, `/auth/`.
- It does **not** disallow `/` or `/events/`. Confirm by reading the served
  file, not the source — a `Disallow: /` shipped by accident de-indexes the
  whole site, and this is the one change here that can do real damage.
- `HEAD /robots.txt` behaves consistently with W-005's outcome, whichever
  mechanism that ticket lands on.
- The changelog entry names the belief being corrected: not "we forgot a file"
  but "a missing `robots.txt` is neutral" — it is not, it is permissive, and
  this site has surfaces that should not be crawled.

## Out of scope

- **`sitemap.xml` — deliberately.** It is DB-driven generation over 356 events
  with their own URLs, with a caching and freshness question attached. A static
  text file and a generated index are different work at different risk.
  **Ticketed as `W-010` (p3, PM 2026-08-28)** — the call this ticket left
  pending is taken: a sitemap is wanted, because PLAN ticket 2 already put
  `short_description` outside the auth gate to be crawlable. The split
  stands; only the "pending" does not. **Do not add a `Sitemap:` line to
  `robots.txt` here** — it 404s until W-010 ships, and W-010 owns that line.
- **Any change to what is behind the auth gate.** This ticket asks crawlers not
  to index those pages. It does not change who can reach them, and `robots.txt`
  is not an access control — do not treat it as one.
- **Meta/SEO work on the event pages.** That is PLAN.md ticket 2.

## Verdict

**VERDICT: APPROVED** — 2026-10-24. Constant `text/plain` body on a
`GET`/`HEAD` route (W-005's mechanism): `User-agent: *`, `Disallow:` for
`/settings`, `/profile`, `/crews`, `/auth/`. No `Disallow: /`, no
`Sitemap:` (W-010). The served file, not the source, went through
`urllib.robotparser`: `/`, `/events/…`, `/stats`, `/privacy` and
`/static/…` were allowed, and every surface in the ticket was blocked.
Prefixes without a trailing slash catch no public route (checked against
the branch's route list). Served from `:8006`, with `/proc/<pid>/cwd` →
`irw-W006`, anon and signed in. The changelog names the corrected
belief ("missing is neutral") and does not claim access control or
de-indexing. Ticket is `deploy: batched`. Routed check 15.

**Not verified:** how real crawlers behave. `robotparser` is not
Google's parser, though with only `Disallow` lines the two agree. A
disallowed URL linked from elsewhere can still be indexed by URL alone;
robots.txt stops the fetch, not the listing. Nothing shows a join-token
URL in any index, so this is the ticket's stated limit, not a gap. The
effect on `/auth/google*` bot traffic is visible only in production
logs, about a day after deploy (crawlers cache robots.txt).
