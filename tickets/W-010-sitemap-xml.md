# W-010 — `/sitemap.xml` 404s on a site whose event pages are meant to be found

**Priority:** 3 · **Effort:** M · **Area:** routing · **Deploy:** batched
**Source:** `AUDIT_20260828T0812.md` F3 (the half W-006 deliberately excluded)
**Depends on:** W-006 (`robots.txt` must exist before it can point at this)

## What is wrong

Not "there is no sitemap." The defect is that **this repo has already
decided organic search is a goal and then shipped only half the mechanism
for it.** `docs/PLAN.md` ticket 2 put `short_description` outside the
auth gate *specifically so it would be crawlable*, and added a
`<meta name="description">` to `event.html` to go with it. That is the
on-page half. The discovery half — telling a crawler that 356 event URLs
exist — was never built, and nothing records that as a decision.

So the current state is: pages optimised to rank, reachable only by a
crawler following links inward from `/`. The event pages are behind a
filtered index that is itself a query surface. Whether a crawler walks
that reliably is not something this repo has ever checked.

**W-006 is not this ticket and the split was correct.** A static text
file with fixed contents and a DB-driven document regenerated as the
corpus changes are different work at different risk. W-006 is `S` and
safe; this is `M` and has a freshness question in it. W-006 left it
"unticketed pending a call" — this ticket **is** that call, and W-006's
instruction not to add a `Sitemap:` line pointing at a 404 stands until
this ships.

## Evidence

Audit F3, live check:

```
/robots.txt  -> 404
/sitemap.xml -> 404
```

The auditor was explicit that it could not price this:

> Whether this matters depends entirely on whether organic search is a
> goal for this product, which I have no basis to judge — flagging the
> state, not prescribing the fix.

`docs/PLAN.md` ticket 2 settles what the auditor could not:

> 1. **Visible prose** in a new anon-accessible block directly below the
>    hero, above the action bar. Outside the `{% if current_user %}` gate —
>    the ticket is explicit that this must be crawlable.
> 2. **`<meta name="description">`** via a new `{% block head %}` in
>    `event.html`, truncated to ~160 chars on a word boundary. This is the
>    actual SEO mechanism; visible text alone is not.

Scale, measured 2026-08-28 against
`core.v_denormalized_event_data_upcoming`: **1724 rows / 356 events**,
i.e. 356 event URLs plus a handful of static pages. Well inside the
50,000-URL / 50 MB limit for a single sitemap file — **no sitemap index
is needed**, and building one would be speculative complexity.

## Acceptance

- `GET /sitemap.xml` returns 200 with `Content-Type: application/xml`
  and a valid `<urlset>` in the `sitemaps.org/schemas/sitemap/0.9`
  namespace.
- It lists the **anon-reachable** URLs only: `/`, `/imprint`, `/privacy`,
  `/terms`, and one entry per upcoming event. **No `/settings`,
  `/profile/*`, `/crews/*`, `/auth/*`** — the same surfaces W-006
  disallows. A sitemap that contradicts `robots.txt` is worse than
  neither.
- URLs are absolute, `https://indierunners.co`, matching the canonical
  host exactly — the apex/`www` question is settled the same way the
  deployed domain resolves, not by guess.
- Every URL in it returns 200 for an **anonymous** client. Spot-check at
  least three event URLs signed out, not just signed in.
- The event set comes from the same service the index page reads, so a
  URL cannot appear in the sitemap that the site would not render.
- The developer states the **freshness mechanism chosen and why**: served
  live per request, or cached with a TTL. Both are defensible at 356
  rows; picking one silently is not. If cached, the TTL is named in the
  changelog and in `ARCHITECTURE.md`.
- `robots.txt` gains its `Sitemap:` line **in this ticket**, not W-006.
- `HEAD /sitemap.xml` behaves consistently with whatever W-005 landed on.
- `docs/CHANGELOG.md` version bumped; `docs/ARCHITECTURE.md` gains the
  route and the freshness decision; `docs/FILE_TREE.md` if a file is added.

## Out of scope

- **`lastmod`, `changefreq` and `priority`.** Optional, widely ignored by
  Google, and `lastmod` in particular is a lie unless it tracks a real
  per-event modification timestamp this app does not currently read.
  Emitting a fabricated one is worse than omitting it.
- **A sitemap index / multiple files.** 356 URLs is two orders of
  magnitude below the threshold. Revisit if the corpus passes ~25,000.
- **Past events.** The serving view is `_upcoming`; an event that has
  happened dropping out of the sitemap is correct behaviour, and
  designing URL permanence for past events is a separate product
  question nobody has asked.
- **Submitting the sitemap to Search Console**, or any registration with
  a search engine. That is an operator action, not a code change, and it
  needs an account decision.
- **Changing what is behind the auth gate**, and any on-page SEO beyond
  the `Sitemap:` line — PLAN ticket 2 already shipped that half.

## Verify

There is no test suite. So, explicitly:

- `curl -s https://<local> /sitemap.xml` parses as XML — pipe it through
  `xmllint --noout -` and let it fail loudly.
- Count the `<loc>` entries and compare against the event count the index
  page renders for an anon user. They must agree.
- Fetch three of the listed event URLs **signed out** and confirm 200.
- Confirm no listed URL matches a `Disallow` rule in the `robots.txt`
  W-006 shipped. This is the check that catches a drift between the two
  files later.

## Verdict

**VERDICT: APPROVED** — 2026-10-25. `GET`/`HEAD /sitemap.xml` returns a
0.9 `<urlset>` of `/`, `/stats` (added on Paulo's say-so, which is outside
this spec), `/imprint`, `/privacy`, `/terms`, plus one apex URL per event
from `list_races(RaceFilters())`. That is the same query and the same
`Race` view `event_detail` reads, so the claim that it "cannot list an
event the site would not render" holds. Freshness is **live per request**,
and the reason is in ARCHITECTURE § Crawl surface. `robots.txt` gains
`Sitemap:`. The verification ran on the served bytes, from `irw-W010`
(confirmed by cwd): all 395 URLs got a `200` anonymously, `robotparser` on
the served file blocked none of them, and a signed-in fetch returned a
byte-identical file.
**Spec amended:** the Verify step "count `<loc>` against the anon index"
is wrong, because the index stops at 60 (W-037). The right comparison is
`len(list_races)`, which the developer used (390 = 390). Ticket is
`deploy: batched`. Routed check 16, and check 15 amended for the
`Sitemap:` line.

**Not verified:** XML/URL safety for a slug outside `[a-z0-9_-]`. `escape()`
handles `&<>`, but nothing percent-encodes, and no current slug exercised
either path. Slugs come from the scraper's unidecode generator, not a DB
constraint. Whether Google fetches it or indexes more event pages: that
is a Search Console question, out of scope.
