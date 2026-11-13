# Routed checks — the PM's messages to the auditor

**Written by the PM. Read by the auditor every sweep. Edited by neither
the auditor nor anyone else.**

This file exists because a prediction written for the auditor had no path
to the auditor. `pm.md` told the PM to write what a fix should change in
production into the ticket's "Not verified" paragraph, "where the auditor
can read it" — and `auditor.md` routes the auditor to their previous
report and nothing else. Ticket verdicts are never read. The handoff was
described in one brief and absent from the other.

Ported from `indie-runners-scraper`, which found the same gap the
expensive way: an auditor filing a shipped fix as a regression, correctly
by their own rules, because the prediction never reached them.

The rule is right. The input was missing.

## Two owners, one file

| Part | Owner |
|---|---|
| This header — the contract, what an entry must carry | chief of staff |
| Every entry below it | **PM** |

It is not under `docs/roles/` because the PM needs a way to tell the
auditor something without write access to a brief, and without filing a
request and waiting.

## What an entry must contain

Naming a ticket id is not enough. A routed check that names `W-0xx` is
not a routed check that carries what will change in production; the
auditor cannot open a ticket verdict and is not asked to.

Four fields. An entry missing one can fail the way this file exists to
prevent. This file is public (README § Boundaries): a signature names the
query and the shape of the row, never a crew slug, a user id or a count.

- **Gate — when it applies, stated as something verifiable.** An image,
  not a date (a date does not survive a rollback), and not "the first
  revision after the merge": an infra apply or a config change makes a
  new revision on the old image (checks 21, 23, 44). Name the revision
  serving at merge time (`./scripts/deploy.sh --check`); the gate is the
  first revision after it whose `status.imageDigest` differs from its. Once the deploy output or a sweep
  names that revision, put it in the header. `auditor.md` has the
  commands.
- **Signature — what will look different, and where.** The page, the
  query, the status code, the direction of a number. Not "expect
  changes" but "`HEAD /` returns 200 where it returned 405".
- **Reading — both directions, explicitly.** Which observation is the
  expected one and must be reported as confirmation, and which is the
  genuine finding. An entry that says only what to expect leaves the
  auditor to infer what its absence means.
- **Retire — what closes it.** A condition, not a feeling. Closed
  entries **stay in this file with their annotation**; they are not
  deleted. A check reporting nothing looks suspicious again months
  later, and the annotation is the evidence that its silence is
  legitimate. Put the retirement in the entry's **header**, which is
  authoritative over everything below it: a retired entry is not swept
  at all, and a decision buried under text that still reads live has not
  been communicated.

**An entry's header carries its status from the day it is written:**
`· LIVE`, with the gate deciding when it applies, until it becomes
`· RETIRED <date>, <evidence>`. There is no third state: `PENDING DEPLOY`
(checks 4 to 7) needed someone to change it at deploy time, nobody owns
that moment, and the auditor sweeps only LIVE entries. A header with no
status is reported and swept as LIVE.

**Numbering is stable.** Sweeps cite these by number across reports, and
the auditor reads their previous report every sweep. New entries take the
next free number; closed ones keep theirs.

**With no test suite here, this file carries more than it does next
door.** "Verified" in this repo means someone ran it once, in a browser,
before merging. A routed check is the only thing that looks again.

---

## The checks

### 1 — `HEAD` answers like `GET` (W-005) · RETIRED 2026-10-24, confirmed under `00056-67l` (AUDIT_20261023T1719)

- **Gate:** serving revision is `indie-runners-web-00052-9k6` or newer
  (deployed 2026-10-21 from commit `9daa5db`; W-008 means the revision
  does not carry the SHA itself).
- **Signature:** `HEAD /`, `HEAD /privacy` and `HEAD` on an event page
  return 200 where they returned 405. `HEAD /settings` anon returns 401,
  the same as `GET` (303 under check 11's gate, also the same as `GET`). The real HEAD 405s in the request log (Chrome/96
  monitor, ShapBot) stop.
- **Reading:** 200 on those pages is **confirmation**. Report it once,
  then stop reporting it. A 405 on any public `GET` page under the gate
  is the **finding**: a regression, or a route added without
  `methods=["GET","HEAD"]`. A 405 on `POST`-only routes or
  `/debug/health` is expected, not a finding.
- **Retire:** the first sweep that confirms it under the gate.

### 2 — the `uuid = character varying` 500 is gone (W-007) · RETIRED 2026-10-26, confirmed under `00060-bgv` (AUDIT_20261025T0713): `transylvania_100`, added after the gate, rendered

- **Gate:** the same revision as entry 1.
- **Signature:** zero log lines matching
  `operator does not exist: uuid = character varying` on revisions under
  the gate. Before the deploy, it was a latent 500 on the first render of
  an event with no image row.
- **Reading:** absence is weak evidence on its own, because the trigger
  only fires when the scraper adds events. It counts as **confirmation**
  only once the sweep can name at least one event added after the gate
  that has rendered. Any occurrence under the gate is the **finding**.
- **Retire:** confirmed as above, or two sweeps under the gate with new
  events and zero matches.

### 3 — profile links resolve (W-019) · RETIRED 2026-10-26, confirmed twice: `00056-67l` (AUDIT_20261023T1719) and `00059-z4t` (AUDIT_20261024T1150)

- **Gate:** serving revision is `indie-runners-web-00053-rnp` (created
  2026-10-21T11:32Z, merge `a0fd9d4`) or newer.
- **Signature:** every event link a profile renders returns 200. To check
  without signing in: in the read-only session, list the
  `(event_slug, occurrence_year)` pairs from `web.attendance` joined to
  `core.events` / `core.event_occurrences` **that also exist in
  `core.v_denormalized_event_data_upcoming`** (the predicate the profile
  now links on), then `GET` each `/events/<slug>/<year>`. Count the
  attendance rows left unlinked, for continuity: there were 14 of 24
  distinct links on 2026-10-21.
- **Reading:** all 200 is **confirmation**. Any 404 is the **finding**,
  most likely `event_detail` and `_load_rows` disagreeing (the coupling
  the W-019 changelog names). A rising unlinked count is **not** a
  finding here; it is F6/W-012, upstream. The request log is weak
  evidence either way: it showed zero profile-referred `/events/` 404s in
  the 7 days *before* the fix, so few people click these links.
- **Retire:** two consecutive sweeps under the gate with all 200.

### 4 — the tile price is a range, not one race with a `+` (W-016) · RETIRED 2026-10-22, confirmed under `00054-2zv`

*Run by the PM, signed out, 2026-10-22, on `00054-2zv` (100% traffic,
created 11:26Z, after both merges). `3kings3hills` `EUR 25.0 – 199.0`,
Dresden Marathon `Free – EUR 185.0`, Kat 100 `—`. Unfiltered index:
53 fees, 0 ending in `+`, 0 containing `None`. Not checked signed in:
no production cookie. The price label does not branch on tier.*

- **Gate:** the first serving revision created after W-016's merge into
  `master` (`deploy: batched`; W-008 means the revision carries no SHA,
  so compare its creation time with the merge commit's).
- **Signature:** no index tile's entry fee ends in `+`. `3kings3hills`
  reads `EUR 25.0 – 199.0` (was `EUR 159.0+`). Dresden Marathon reads
  `Free – EUR …` (was `EUR 10.0+`). `kat_100` reads `—` (was
  `None 77.95+`). Check each with `GET /?search=<name>`, signed out.
- **Reading:** a range, or a single value with no `+`, is
  **confirmation**. A `+` or the text `None` on any tile under the gate
  is the **finding**. An event leaving the view (F6) is not a finding
  here. Neither is a changed range: prices move upstream.
- **Retire:** the first sweep that confirms it under the gate.

### 5 — the date filters judge TBC events by expected month (W-020) · RETIRED 2026-10-22, confirmed under `00054-2zv`

*Run by the PM, signed out, 2026-10-22, on `00054-2zv`. With
`date_from=2027-01-01`, Comrades and Plaenterwaldlauf appear. With
`date_to=2026-12-31`, Valentislauf is gone (present unfiltered), and
`search=athens` returns only the non-TBC Athens Authentic. Zero 5xx and
zero ERROR logs on the revision. Not checked signed in, as above.*

- **Gate:** the first serving revision created after W-020's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** signed out, `GET /?date_from=2027-01-01&search=comrades`
  shows Comrades Marathon (expected June 2027), where before the deploy
  it did not. `GET /?date_to=2026-12-31&search=valentislauf` shows
  nothing, where before it showed the tile.
- **Reading:** both as stated is **confirmation**. The reverse of
  either, under the gate, is the **finding**. An event that has left the
  view or changed its expected month since 2026-10-22 is neither. Pick
  another TBC event expected in 2027 and say which.
- **Retire:** the first sweep that confirms it under the gate.

### 6 — `www.` and `beta.` redirect permanently (W-017) · RETIRED 2026-10-24, confirmed under `00056-67l` (AUDIT_20261023T1719)

- **Gate:** the first serving revision created after W-017's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** `curl -sI https://www.indierunners.co/` and
  `https://beta.indierunners.co/` return `301` with
  `location: https://indierunners.co/`, where both returned `302` on
  2026-10-22. A path and query (`/events/x/2027?a=1`) are carried over
  unchanged. `HEAD https://indierunners.co/` stays `200`. OAuth
  callbacks in the request log still return `307`.
- **Reading:** all of that is **confirmation**. A `302` under the gate
  means the deploy did not carry the change. A redirect loop, an apex
  answering `301`, or callbacks failing are the **finding**, and the
  urgent kind: a rollback will not clear a cached 301 from browsers.
- **Retire:** the first sweep that confirms it under the gate.

### 7 — `/favicon.ico` stops 404ing (W-024) · RETIRED 2026-10-24, confirmed under `00056-67l` (AUDIT_20261023T1719)

- **Gate:** the first serving revision created after W-024's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** `curl -sI https://indierunners.co/favicon.ico` returns
  `307` to `/static/brand/favicon/favicon.ico`, which returns `200`.
  `/favicon.ico` 404s in the request log go to zero on that revision
  (69 in the 7 days to 2026-10-22).
- **Reading:** both is **confirmation**. Any `/favicon.ico` 404 under
  the gate, or a 404 on a `/static/brand/favicon/` path, is the
  **finding**. Old revisions still in the log window are not.
- **Retire:** the first sweep that confirms it under the gate.

### 8 — `/stats` exists, and `Race` maps `event_last_checked_at` (W-025) · RETIRED 2026-10-26, confirmed under `00059-z4t` (AUDIT_20261024T1150)

- **Gate:** the first serving revision created after W-025's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** `GET /stats` and `HEAD /stats` return `200` anon, where
  both returned `404`. The page shows "events tracked", "events checked
  in the last 30 days" and "Recently checked" with 10 rows, newest first,
  each linking to a `200` event page. Every footer carries a Stats link.
  "Events tracked" equals `count(*) FROM core.events WHERE status =
  'active'` (491 on 2026-10-22). Because every `Race` select now reads the
  new column, `/`, an event page and a profile also stay `200`.
- **Reading:** all of that is **confirmation**. A lower 30-day count or a
  different event at the top of the list is **not** a finding: runs are
  bursty (11 of 30 days had none), so both churn every sweep. A `404`
  under the gate means the deploy did not carry the change. The
  **finding** is a `500` anywhere (urgent: it would be the mapping, on
  every page), a link that 404s, a headline that disagrees with the
  query, or the two counts shown as one number or a fraction.
- **Retire:** the first sweep that confirms it under the gate.

### 9 — a user can delete their own account (W-022) · RETIRED 2026-10-26, confirmed under `00059-z4t` (AUDIT_20261024T1150)

- **Gate:** the first serving revision created after W-022's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** `curl -s https://indierunners.co/privacy` §8 links
  "Settings → Delete account" and says "up to 7 days". The sentence
  "is planned but not yet available" is gone. Anon `POST
  /settings/delete-account` returns `401`, not `404` or `405`.
  `gcloud sql backups list --instance indie-runners-db` shows only
  `AUTOMATED` backups, 7 at most.
- **Reading:** all of that is **confirmation**. A `web.users` count
  lower than the last sweep's is **not** a finding: deletion is now
  self-serve. The **finding** is any of these: a `500` on `/settings`,
  `/privacy` or the delete route; a `403` on `POST
  /settings/delete-account` in the request log, which most likely means
  production `Host` does not match `Origin`, so every delete is refused
  (read the request's headers before calling it an attack); or any
  `ON_DEMAND` backup older than 7 days, which makes §8 false (W-032).
- **Retire:** the first sweep that confirms the signature under the
  gate. The backup line becomes W-032's own check when that ticket ships.

### 10 — the terms name the delete button; both legal pages are dated (W-034) · RETIRED 2026-10-26, confirmed under `00059-z4t` (AUDIT_20261024T1150)

- **Gate:** the first serving revision created after W-034's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** `curl -s https://indierunners.co/terms` §9 links
  "Settings → Delete account" and still names the email address. Both
  `/terms` and `/privacy` show a `Last revised:` line with the same date,
  where privacy had none and terms read 27 July 2026. Neither page shows
  the text "MAINTAINER".
- **Reading:** all of that is **confirmation**. A terms date of 27 July
  under the gate means the deploy did not carry the change. The
  **finding** is a `500` on either page, the two dates disagreeing, or
  the maintainer comment rendered as text. A signed-out `/settings`
  returning `401` JSON is **known**, not a finding: it is W-035's, until
  W-035 ships.
- **Retire:** the first sweep that confirms it under the gate.

### 11 — a signed-out `/settings` redirects to sign-in, not a JSON 401 (W-035) · RETIRED 2026-10-26, confirmed under `00059-z4t` (AUDIT_20261024T1150)

- **Gate:** the first serving revision created after W-035's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** anon `GET /settings` and `HEAD /settings` return `303`
  with `Location: /auth/google?next=/settings`, where both returned
  `401` `{"detail":"not authenticated"}`. Anon `POST /settings` and
  `POST /settings/delete-account` still return `401`.
- **Reading:** all of that is **confirmation**. A `303` here is not a
  regression of check 1, which this entry supersedes for `/settings`.
  It also retires check 10's "known" note. A `401` on anon `GET
  /settings` under the gate means the deploy did not carry the change.
  The **finding** is a `500` on `/settings`, a `Location` that is not
  that exact path, a POST answering `303` or `200` signed out, or a
  redirect loop: repeated `/settings` ↔ `/auth/google` from one client
  in the request log.
- **Retire:** the first sweep that confirms it under the gate.

### 12 — `/stats` carries a coverage map whose every link lands on tiles (W-026) · RETIRED 2026-10-26, confirmed under `00059-z4t` (AUDIT_20261024T1150)

- **Gate:** the first serving revision created after W-026's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** signed out, `GET /stats` shows "Upcoming events by
  country": a Europe map with shaded countries and a ranked list of
  names and counts. On 2026-10-23 it listed 42 countries and shaded 39
  (US, South Africa and Comoros are list only). Each list link is
  `/?country=<name>`, and `GET` on it returns at least one tile. Below
  60, the "Showing N races" count equals the listed count.
- **Reading:** the map and list rendering, with every link non-empty, is
  **confirmation**. A listed country whose link returns zero tiles, or a
  sub-60 count that disagrees with the click, is the **finding**: the
  `/stats` count and the index query have drifted apart (see the 1.9.18
  changelog). A count above 60 whose click says "Showing 60" is
  **known** (W-037), not a finding. Counts that move between sweeps are
  upstream. A `500` on `/stats` is the finding, and check 8 covers it
  too.
- **Retire:** the first sweep that confirms it under the gate.

### 13 — "Recently checked" shows a time in UTC (W-039) · RETIRED 2026-10-26, confirmed under `00060-bgv` (AUDIT_20261025T0713)

- **Gate:** the first serving revision created after W-039's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** signed out, every "Recently checked" row on `GET
  /stats` ends `— last checked <d Mon YYYY>, <HH:MM> UTC`, where it
  ended at the year. For the top row, `max(event_last_checked_at) AT
  TIME ZONE 'UTC'` for that event, read-only, gives the same date and
  minute.
- **Reading:** a time equal to the query is **confirmation**. A row
  with a date only means the deploy did not carry the change. The
  **finding** is a rendered time off the query by a whole number of
  hours (the zone is not being converted), a `500` on `/stats`, or the
  literal `UTC` missing. A different event at the top is not a
  finding: checks are bursty (see 8).
- **Retire:** the first sweep that confirms it under the gate.

### 14 — a finished edition's URL redirects to the next edition, not a JSON 404 (W-040) · RETIRED 2026-10-26, confirmed under `00060-bgv` (AUDIT_20261025T0713)

- **Gate:** the first serving revision created after W-040's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** `GET` and `HEAD /events/grand_trail_templiers/2026`
  return `302` with `Location: /events/grand_trail_templiers/2027`,
  where both returned `404` `{"detail":"Event not found"}`. A made-up
  slug returns `404` `text/html` containing "We couldn't find this
  event". In the request log, `GET 404` on `/events/<slug>/<year>`
  shrinks to slugs the view has no edition of.
- **Reading:** all of that is **confirmation**. A `404`
  `application/json` on a slug with a live edition means the deploy did
  not carry the change. The **finding** is a `302` whose `Location` does
  not itself return `200` (a loop or a dead target), a `301`, or a `500`
  on the route. Not findings: crawlers still requesting `/2026` URLs (a
  302 never tells them to forget); a `200` on a just-finished edition's
  URL once scraper T-134 ships D+2 rows; a JSON 404 on `/crews/<slug>`
  (out of W-040's scope).
- **Retire:** the first sweep that confirms it under the gate.

### 15 — `/robots.txt` is served and keeps compliant crawlers off the signed-in surfaces (W-006) · RETIRED 2026-10-28, confirmed under `00064-l84` (AUDIT_20261028T1006): body exact; 0 hits from the five named crawlers on the disallowed paths in 24h. GPTBot ×2 is not one of the five and was not chased. F3's `meta-externalagent` burst never fetched robots.txt, so it is not this check's (dropped at triage: one 4-minute burst of bare 307s, no DB read)

- **Gate:** the first serving revision created after W-006's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** `GET` and `HEAD /robots.txt` return `200`
  `text/plain`, where both returned `404`. The body is exactly
  `User-agent: *` plus `Disallow:` lines for `/settings`, `/profile`,
  `/crews` and `/auth/`. In the request log, `robots.txt` 404s go to
  zero (35 in 24h on 2026-10-21). From about 24h after the gate, hits on
  `/auth/google*` from crawlers that fetch robots.txt (Amazonbot,
  Baiduspider, bingbot, Googlebot, OAI-SearchBot) fall toward zero. On
  2026-10-21 there were 45+ in 7 days.
- **Reading:** a `200` with that body, and those crawlers leaving
  `/auth/`, `/crews/`, `/profile` and `/settings`, is **confirmation**.
  A `404` means the deploy did not carry the change. The **finding** is
  any line reading `Disallow: /` alone or `Disallow: /events`, a
  non-`200` on `/robots.txt`, or a drop in crawler hits on
  `/events/<slug>/<year>`. A compliant crawler still hitting a
  disallowed path more than 48h after the gate is also a finding. Not a
  finding: bots that never fetch robots.txt, or that ignore it, still
  hitting those paths. robots.txt is not access control. A trailing
  `Sitemap: https://indierunners.co/sitemap.xml` line is expected once
  W-010 is in the revision (check 16), and its absence before then is
  not a finding either. *PM 2026-10-26:* exclude the iPhone/iOS 13.2.3
  client that requests `/auth/google` every ~10 minutes (AUDIT_20261026T0807
  F6). It is not a named crawler, and the route is a bare `307` with no
  DB read (`google_login`, `app/main.py`), so it is noise, not a finding.
- **Retire:** the first sweep at least 48h after the gate that confirms
  both the body and the fall in `/auth/google*` crawler hits.

### 16 — `/sitemap.xml` is served and lists only pages that answer 200 anonymously (W-010) · RETIRED 2026-10-26, confirmed under `00061-kkm` (AUDIT_20261026T0807)

- **Gate:** the first serving revision created after W-010's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** `GET` and `HEAD /sitemap.xml` return `200`
  `application/xml` where both returned `404`. It is a sitemaps.org 0.9
  `<urlset>` of `<loc>`-only entries: `/`, `/stats`, `/imprint`,
  `/privacy`, `/terms`, plus one `https://indierunners.co/events/<slug>/<year>`
  per upcoming event (390 on 2026-10-25). `/robots.txt` ends with
  `Sitemap: https://indierunners.co/sitemap.xml`. `sitemap.xml` 404s in
  the request log go to zero.
- **Reading:** the following is **confirmation**: a `200`, a parseable
  body, an event `<loc>` count within a few of the index's pre-cut event
  count, and every sampled `<loc>` (at least 10) returning `200` signed
  out. A `404` means the deploy did not carry the change. The
  **finding** is any of: a `<loc>` on a host other than the apex; any
  `<loc>` under `/settings`, `/profile`, `/crews` or `/auth/`; a sampled
  `<loc>` answering anything but `200` (a `302` is a finished edition
  the sitemap should have dropped); a `5xx` on the route; or a body that
  fails to parse. Not findings: no `lastmod` (deliberate), and no change
  in crawler traffic to event pages within a week (Google's pace).
  *PM 2026-10-26, on F5 (381 `<loc>`s, 386 slugs in the view):* not a
  gap. The sitemap is built from `list_races` itself, which leaves out
  view events whose rows are all past. Compare with the index, not with
  `count(DISTINCT event_slug)` on the view.
- **Retire:** the first sweep that confirms it under the gate.

### 17 — profile rows show a location line and a terrain badge, read from the MV (W-027) · RETIRED 2026-10-26 — DB half and log half confirmed under `00061-kkm` (AUDIT_20261026T0807); the badge is not auditor-visible (see Reading); the MV-recreate tripwire moved to 18

- **Gate:** the first serving revision created after W-027's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** a signed-in `/profile/<id>` row carries
  `profile-race-sub` (location) and `profile-terrain-badge` where it
  carried neither. `/profile/*` now reads `core.mv_denormalized_event_data`
  directly, the first web read of the MV. In the DB: of the attendance rows
  whose `event_id` has an MV row, nearly all have a non-NULL `terrain_type`
  there (46/46 terrain, 45/46 location on 2026-10-25).
- **Reading:** badges on rows, and no 5xx on `/profile/*`, is
  **confirmation**. Report it once. The **finding** is any of: a 5xx on
  `/profile/*` whose log says `permission denied` or `column ... does not
  exist` on the MV (a scraper MV rebuild changed grants or columns; route
  to the scraper and cite its IDEAS entry of 2026-10-25); an empty
  `profile-race-sub` div or an empty badge; or rows with neither on a
  profile whose events the MV holds. Not findings: Spartathlon showing no
  location (the MV has none), and a neutral grey badge for `mixed` or
  `other` (only trail and road have colours).
  *PM 2026-10-26:* the badge half needs a cookie, because a signed-out
  viewer gets the placeholder for every profile by design
  (`ProfileService._can_view`). It was checked in the browser at the W-027
  review. Confirmation for the auditor is the DB half plus real
  `/profile/*` `200`s with no 5xx and no `permission denied`, which
  AUDIT_20261026T0807 reported.
- **Retire:** the first sweep under the gate that confirms it, and also
  after the next scraper migration that recreates the MV, if no 5xx
  follows it. *The second half is now check 18's: scraper T-147 is that
  migration.*

### 18 — Kosovo and Reykjavik get real country names, upstream (scraper T-147) · LIVE — waiting on the scraper

- **Gate:** in the view, `event_country_code` for `prishtina_marathon`
  is no longer `xk`. Scraper T-147 makes the change: a data fix plus a
  full recreate of `core.mv_denormalized_event_data`. This repo changes
  nothing.
- **Signature:** `/stats` and the index's country dropdown list
  "Kosovo" where they list "Xk", and Reykjavik Marathon is counted
  under Iceland, not Comoros. Comoros leaves the list.
- **Reading:** before the gate, "Xk" and Comoros are **known**. They
  were routed 2026-10-24 and are scraper T-147, not a finding, and not
  this repo's (AUDIT F1 has filed them here three sweeps running). After
  the gate, the names above are **confirmation**. The **finding** is a
  real name in the view with a raw code on the page (this repo's
  mapping), `/?country=kosovo` returning no tile, or any 5xx on
  `/profile/*` (`permission denied`, `column ... does not exist`) after
  the MV recreate, which routes back to the scraper. No view row for
  `prishtina_marathon` or `reykjavik_marathon` means its edition ended:
  not a finding, and the gate cannot be read until the row returns.
- **Retire:** the first sweep after the gate that confirms the names and
  sees no `/profile/*` 5xx since the recreate.

### 19 — a one-day edition's hero shows one date, not "29 May – 29 May" (W-047) · RETIRED 2026-10-28, confirmed under `00064-l84` (AUDIT_20261028T1006)

- **Gate:** the first serving revision created after W-047's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** signed out, the hero of `GET /events/transylvania_100/2027`
  reads `29 May`, where it read `29 May – 29 May`. The hero of
  `night_marathon_luxemburg/2027` still reads `7 May – 8 May`. Across at
  least 25 sampled event `<loc>`s from `/sitemap.xml`, no hero shows the
  same date on both sides of the dash (153 of 234 dated occurrences did on
  2026-10-26).
- **Reading:** one date on a same-day edition, and ranges kept on
  multi-day ones, is **confirmation**. A doubled date under the gate
  means the deploy did not carry the change. The **finding** is a
  multi-day edition showing one date (that would be bad data upstream,
  so route it to the scraper with the slug), a dated non-TBC event whose
  hero shows no date at all, or a `500` on `/events/*`. Not findings:
  either named slug leaving the view (pick another), or a TBC hero, which
  this did not change.
- **Retire:** the first sweep that confirms it under the gate.

### 20 — the index says "Showing 60 of N races" when the 60-tile cap cuts (W-037) · RETIRED 2026-10-28, confirmed under `00064-l84` (AUDIT_20261028T1006)

- **Gate:** the first serving revision created after W-037's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** signed out, `.filter-results` on `GET /` reads
  `Showing 60 of N races` where it read `Showing 60 races` (N was 381
  locally on 2026-10-26). `/?country=germany` reads `Showing 60 of N`,
  where N is Germany's count on `/stats` (98 on 2026-10-26). A country
  under 60 on `/stats` (for example France) still reads `Showing N races`,
  with N tiles.
- **Reading:** "of N" above the cap, and none at or below it, is
  **confirmation**. Under the gate, `Showing 60 races` on `/` means the
  deploy did not carry the change. The **finding** is "of N" where N is
  not more than the tile count, a country's N that differs from `/stats`
  by more than the view-vs-`list_races` gap W-038 names, or a `500` on
  `/`.
- **Retire:** the first sweep that confirms it under the gate.

### 21 — a taken crew name is refused, not suffixed (W-041) · RETIRED 2026-11-03, confirmed under `00080-vml` (AUDIT_20261103T0806): a crew created 2026-11-02T13:34Z, 0 suffixed slugs, 0 duplicate names. `crews` fell 4 → 3 with one created; no app route deletes a crew and no account was deleted; Paulo confirmed 2026-11-03 he deleted the two by hand · gate was met by `00063-9xj` (created 2026-10-27T09:06Z, built from `714e36c`, app code = master), **not** `00062-5ls`: that is I-011's infra apply, created after these merges on `00061`'s image (same digest `4d3c39d6`) (triage 2026-10-27)

- **Gate:** the first serving revision created after W-041's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** in `web.crews` (counts only), one `lower(trim(display_name))`
  value is held by more than one row: the existing pair. That number does
  not grow. No row created under the gate has a slug matching `-[0-9]+$`
  whose base slug is also a row. Request log: a `POST /crews/new` that
  returns 400 is the refusal working (it is also the short-name message,
  so it is not proof on its own).
- **Reading:** if the existing pair is still there, that is **expected**.
  Renaming it waits on Paulo's `UPDATE`. If it disappears, that is the
  `UPDATE`, not a finding. The **finding** is a second duplicated name, or
  a new suffixed slug, under the gate. Either one means the deploy did
  not carry the change, or something else writes crews.
- **Retire:** the first sweep under the gate that sees at least one crew
  created after it and the duplicate count still 1 (or 0 after the
  `UPDATE`). If no crew has been created since the gate, report it as
  "live, not exercised", not as confirmed.

### 22 — the footer links the Strava club and the Instagram account (W-046) · RETIRED 2026-10-28, confirmed under `00064-l84` (AUDIT_20261028T1006)

- **Gate:** the first serving revision created after W-046's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** the HTML of `GET /` (and any page, since it is
  `base.html`) has a `<footer>` that contains
  `href="https://www.strava.com/clubs/2244858"` and
  `href="https://www.instagram.com/weareindierunners/"`, each with
  `rel="noopener noreferrer"`.
- **Reading:** both hrefs present under the gate is **expected** and
  confirms the deploy. The **finding** is either href missing, or a
  different URL. A 403 from the Strava URL to curl is **not** a finding:
  Strava walls bots and returns 200 only to browser headers.
  *PM 2026-10-26:* W-050 swaps the link text for logos and keeps the
  hrefs and `rel`. Under a revision that carries W-050, a missing word
  "Strava" or "Instagram" is **not** a finding; the hrefs still are.
- **Retire:** the first sweep under the gate that sees both hrefs in the
  footer of `/`.

### 23 — a crew name the slug cannot hold is refused, not served blank or as a 500 (W-049) · RETIRED 2026-11-03, confirmed and exercised under `00080-vml` (AUDIT_20261103T0806): `new` 0, over 64 chars 0, and `POST /crews/new` answered 303 under the gate · gate was met by `00063-9xj` (created 2026-10-27T09:06Z, built from `714e36c`, app code = master), **not** `00062-5ls`: that is I-011's infra apply, created after these merges on `00061`'s image (same digest `4d3c39d6`) (triage 2026-10-27)

- **Gate:** the first serving revision created after W-049's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** in `web.crews` (counts only), rows with `slug = 'new'`:
  0, and rows with `length(slug) > 64`: 0. Request log: no 5xx on
  `POST /crews/new`. A 400 there is a refusal, but short, taken,
  reserved and too-long names all return 400, so a 400 does not prove
  this check on its own (as in 21).
- **Reading:** 0 and 0 is **expected**. It also confirms the instance
  Cloud Run serves matches the one the developer counted. A `new` row
  created **before** the gate is not a finding: it goes to Paulo with
  the count, and renaming it is his `UPDATE`. The **finding** is a `new`
  row created under the gate, or a 5xx on `POST /crews/new` with a
  `DataError` in the request log. Either one means the deploy did not
  carry the change, or something else writes crews. A `DataError` from a
  long `display_name` is W-052, not a regression of this check.
- **Retire:** the first sweep under the gate that sees 0 and 0. The
  baseline was already 0 and 0, so that confirms absence, not that the
  check fired. Report it as "live, not exercised" unless the request log
  shows a `POST /crews/new` under the gate.

### 24 — the footer's Strava and Instagram links are glyphs on a row of their own (W-050) · RETIRED 2026-10-28, confirmed under `00064-l84` (AUDIT_20261028T1006)

- **Gate:** the first serving revision created after W-050's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** in the HTML of `GET /`, the `<footer>` holds a
  `<div class="footer-social">` with the two check-22 hrefs. Each has
  `aria-label="Indie Runners on Strava"` / `"…on Instagram"` and an
  `<img src="/static/icons/strava.svg">` / `instagram.svg`. The words
  "Strava" and "Instagram" are gone as link text. `GET` on both SVGs
  returns `200 image/svg+xml`.
- **Reading:** all of that is **expected**. The **finding** is either
  SVG returning anything but `200`, the old text links still present, a
  link without its `aria-label`, or a check-22 href changed. A
  `404` on the SVGs while the markup is present means `static/icons/`
  was not in the image. The layout (the row sitting below) isn't visible
  from `curl`. Don't report it either way.
- **Retire:** the first sweep under the gate that sees the markup and
  both `200`s.

### 25 — a tile's tied-race pick follows `mv_id`, not the query plan (W-029) · RETIRED 2026-10-28, confirmed under `00064-l84` (AUDIT_20261028T1006)

- **Gate:** the first serving revision created after W-029's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** for `tenerife_bluetrail`, the tile's location and
  terrain badge are identical on `GET /?search=bluetrail` and
  `GET /?search=bluetrail&date_from=2027-01-01`. Both equal the first
  row of this read-only query:
  `SELECT race_location, terrain_type FROM core.v_denormalized_event_data_upcoming
  WHERE event_slug='tenerife_bluetrail' ORDER BY coalesce(race_date,
  make_date(occurrence_year::int, coalesce(occurrence_expected_month::int,12), 1)), mv_id LIMIT 1`.
  At review that was Playa de los Cristianos / mixed (the badge reads
  "Mixed"). Before the fix, the filtered URL read La Esperanza / trail.
- **Reading:** both URLs agreeing with the query is **expected**,
  whatever town the query names. The **finding** is the two URLs
  disagreeing, or either one disagreeing with the query. If the event
  has left the view, or no longer has two races on its earliest date,
  the check can't be read: say so, don't report a finding. Don't
  compare against `/?search=Esperanza`: a search on location drops
  races, so a different town there is by design. ~46 default-page
  tiles naming a different town than under `00061` is the deploy's
  intended effect, not a finding.
- **Retire:** the first sweep under the gate that reads both URLs and
  the query in agreement, or that records the check as unreadable
  because the tie is gone.

### 26 — the official-website link sits in the action card, not the hero (W-013) · RETIRED 2026-10-28, confirmed under `00064-l84` (AUDIT_20261028T1006)

- **Gate:** the first serving revision created after W-013's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** anon `GET /events/athens_authentic_marathon/2026` (or
  any event with a website): the `<header class="event-hero">` holds no
  `event-website-link`. Inside `<div class="event-action-bar">`, one
  `<a class="event-website-link">` with the same `href`,
  `target="_blank"`, `rel="noopener noreferrer"` comes after
  `event-description` (when there is one) and before `event-attendance`.
- **Reading:** that is **expected**. The **finding** is the link still in
  the header, the link in both places, or the link missing from the card
  on an event whose `event_website_url` is set. On a TBC page signed in,
  a second "Visit the official website →" in the locked panel is by
  design, not a duplicate. Colour and spacing aren't visible from `curl`;
  don't report them either way.
- **Retire:** the first sweep under the gate that sees the link in the
  card and not in the header.

### 27 — index tiles carry "Registration open" again, from `registration_open` (W-021) · RETIRED 2026-10-29, confirmed under `00065-mzr` (AUDIT_20261029T2231): 0 mismatches of 60 tiles against `bool_or(registration_open)`, no badge on a TBC tile

- **Gate:** the first serving revision created after W-021's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** anon `GET /`: `<span class="badge">Registration open</span>`
  inside `tile-hover` on some tiles, where every earlier revision had none.
  At review it was 37 of 60, but the count follows the data. A tile is
  badged iff `bool_or(registration_open)` over its event's rows in
  `core.v_denormalized_event_data_upcoming` is true and the tile is not TBC.
- **Reading:** badges on non-TBC tiles whose event has an open race are
  **expected**, anon and signed-in alike. Anon is by design (W-021
  verdict). The **finding** is zero badges under the gate while the view
  has open races, a badge on a TBC tile, or a badge on an event whose
  races are all false/NULL.
- **Retire:** the first sweep under the gate that sees badges and no
  mismatch against the view.

### 28 — signed-in "going" offers a Save to Google Calendar popup; anon carries none of it (W-023) · RETIRED 2026-10-28, confirmed under `00064-l84` (AUDIT_20261028T1006)

- **Gate:** the first serving revision created after W-023's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** **none visible anon.** Anon `GET /` and `GET /events/…`
  must carry no `gcal-dialog` element and no `data-gcal-url` attribute,
  same as every earlier revision. The feature only exists signed in: a
  `<dialog class="gcal-dialog">` in every page, and `data-gcal-url` on
  dated tiles and dated event pages.
- **Reading:** anon pages without either string are **expected**. Report
  them as confirmation, not as "feature missing". The **finding** is
  either string in an anon response, because that would mean the
  signed-in gate leaked. If a sweep can see a signed-in page, a TBC tile
  or TBC event with a `data-gcal-url` is a finding. So is a URL whose
  `dates=` end isn't the last date + 1. A tile span shorter than the
  event's under a filter or search is W-061, not a finding here.
- **Retire:** the first sweep under the gate that sees no `gcal-dialog`
  or `data-gcal-url` on anon `/` and one anon event page.
  *PM 2026-10-30:* this retirement confirmed the anon side only; the
  signed-in popup was never swept. Paulo reports it silent on
  `00065-mzr` on both pages, every browser — W-074, `deploy: immediate`.
  Not a finding for this check; W-074's own check follows its fix.
  *PM 2026-10-30, W-074 review:* the cause was a browser-cached pre-W-023
  `attendance.js`, not the revision. See check 35.

### 29 — anonymous attendees render as `avatar--anon-N`, with no identity in the markup (W-028) · RETIRED 2026-10-28, confirmed under `00064-l84` (AUDIT_20261028T1006)

- **Gate:** the first serving revision created after W-028's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** signed out, `GET /` and one event page with attendees
  carry `avatar--anon avatar--anon-N` spans and **zero** `avatar--stock`
  and zero `>ir<`. Each anon span holds exactly `class` and `aria-hidden`
  plus the inline SVG: no `href`, `title`, `src` or `data-*`. The anon
  strip has no `profile/`, `googleusercontent` or `<img`. On 2026-10-27 the
  branch rendered 40 anon circles on `/` (20 `avatar--lg`), where master
  had 40 `avatar--stock`.
- **Reading:** all of that is **confirmation**. `avatar--stock` under the
  gate means the deploy did not carry the change. An identity string
  inside an anon span is the **finding**, and the urgent kind: it breaks
  Paulo's rule that a signed-out visitor can't follow a person by colour
  or markup. No `-3`/`-4` on tiles (cap 3) and no `-4` on the event row
  (cap 4) is **expected**, not missing. The signed-in hidden-attendee
  render can't be swept signed out. Its absence here is not evidence.
- **Retire:** the first sweep under the gate that confirms it on `/` and
  one event page.

### 30 — the sitemap lists the events the index lists, not every event in the view (W-010) · RETIRED 2026-10-29, confirmed under `00065-mzr` (AUDIT_20261029T2231): sitemap 392 = index 392

- **Gate:** serving revision `00064-l84` or newer. Triage 2026-10-28
  settled AUDIT_20261028T1006 F4, so the gap stops being filed.
- **Signature:** `/sitemap.xml`'s `/events/` count equals N in anon `/`'s
  "Showing 60 of N races" (392 and 392 that sweep). It is lower than the
  view's `count(DISTINCT event_slug)` (396) because the sitemap is built
  from `list_races`, whose date predicate (`race_service.py:193-208`)
  drops an event when no row is dated yesterday or later and it is not a
  `tbc` whose expected month is this month or later. The 4 that day:
  `frohnaulauf` (tbc 2023, month 9), `vilnius_half_marathon` (tbc 2026,
  month 5), `kyiv_marathon` and `dublin_marathon` (`current`, no race
  dated, end date 2026-10-25). Routed to the scraper as data.
- **Reading:** sitemap count = index N is **expected**, whatever the gap
  to the view. The **finding** is the two counts differing, a sitemap
  `<loc>` answering non-200 anonymously, or an event reachable as a tile
  on `/` with no `<loc>`. A dropped event's page answering 200 is not a
  finding (the sitemap is a subset, check 16). If the counts split, check
  first for rows with NULL `occurrence_year`: the sitemap skips them
  (`main.py:840`), the index doesn't. That is a web cause, not data.
- **Retire:** the first sweep that confirms the counts match.

### 31 — the event hero's meta row has separators only between items, and the country is title-cased (W-065) · RETIRED 2026-10-29, confirmed under `00065-mzr` (AUDIT_20261029T2231): Athens and `hochkoenigman`. A UK event was not seen

- **Gate:** the first serving revision created after W-065's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** anon `GET /events/athens_authentic_marathon/2026`: the
  first child of `<div class="event-meta">` is an `event-meta-item`
  reading `Greece`, not an `event-meta-sep`. Under `00064-l84` it read
  `· greece · 7 November`. `hochkoenigman/2027` (NULL country) has one
  item, the date, and no `event-meta-sep`. A UK event reads `United Kingdom`.
- **Reading:** no row opening or closing with a separator, and capitalised
  countries, is **confirmation**. A leading `·` or `greece` under the gate
  means the deploy did not carry it. The **finding** is two separators in a
  row, a separator at either end, or a 500 on `/events/*`.
  `Bosnia And Herzegovina` is W-071, not a finding. A location item
  appearing is W-070 or the scraper, not a finding either.
- **Retire:** the first sweep under the gate that confirms Athens and
  `hochkoenigman`.

### 32 — signed-in hidden-attendee line stands alone when nobody is named; anon unchanged (W-066) · RETIRED 2026-10-29, confirmed under `00065-mzr` (AUDIT_20261029T2231), anon only. The signed-in line was never swept

- **Gate:** the first serving revision created after W-066's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** **none visible anon.** An anon event page with attendees
  carries the avatar row only: no `whos-coming-others` element, and no
  `indie runner is` / `indie runners are` (lower case) or `and N other`
  text. Same as every earlier revision. The change is signed in only. A
  column with hidden attendees reads `1 indie runner is going` /
  `N indie runners are going` when nobody is named, or `and N other indie
  runner(s) are going` under names. `interested` replaces `going` in that
  column.
- **Reading:** an anon page without those strings is **confirmation**.
  Don't report it as "feature missing". The **finding** is any of them in an
  anon response, because that means the signed-in gate leaked. If a sweep
  can see a signed-in page: a bare `and N other` with no `indie runner`
  after it, under the gate, means the deploy didn't carry the change. A line
  starting `and` under an empty list is the finding.
- **Retire:** the first sweep under the gate that sees no
  `whos-coming-others` on one anon event page with attendees.

### 33 — one location rule: heroes show a race start town, a tile skips a NULL first-see town (W-070) · RETIRED 2026-11-01, confirmed under `00070-r9n` (AUDIT_20261101T0758): Athens hero `Athens · Greece`, `otf_presented_by` tile `Oberaudorf`, `borsig_half_marathon` `—` with no town on any row

- **Gate:** the first serving revision created after W-070's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** anon `GET /events/athens_authentic_marathon/2026`: the
  first `event-meta-item` in `<div class="event-meta">` reads `Athens`,
  then `Greece`. Under `00065-mzr` the first item was `Greece`. Anon
  `GET /?date_from=2027-09-30&date_to=2027-09-30&country=germany` (the
  60-tile cap hides it otherwise): the `otf_presented_by` tile's Location
  hover row reads `Oberaudorf`, where it read `—`. The hover rows render
  anon. `?search=borsig`: the `borsig_half_marathon` tile reads `—`, and
  its hero has no location item (`Germany · 5 September`).
- **Reading:** a town in the hero and `Oberaudorf` on that tile are
  **confirmation**. A hero town that is **not** any race's
  `race_location` for that event is the scraper's `event_location` (their
  T-039) landing. That is also confirmation, not a regression: the rule
  prefers it. The **finding** is a location item on the hero of an event
  with no `race_location` on any row; `—` on a non-TBC tile whose event
  has a town on any race (the filter on that request can drop races, so
  check with the same filter); or a 500 on `/`, `/events/*` or
  `/profile/*`. A TBC tile with no Location row at all is by design.
- **Retire:** the first sweep under the gate that confirms Athens and
  `otf_presented_by`.

### 34 — the footer's social row carries a third glyph, GitHub (W-067) · RETIRED 2026-11-01, confirmed under `00070-r9n` (AUDIT_20261101T0758): markup in order, SVG `200 image/svg+xml`

- **Gate:** the first serving revision created after W-067's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** in the HTML of `GET /`, `<div class="footer-social">`
  holds three links, in order Strava, Instagram, GitHub. The third is
  `href="https://github.com/indie-runners"` with
  `rel="noopener noreferrer"`, `aria-label="Indie Runners on GitHub"` and
  `<img src="/static/icons/github.svg">`. `GET /static/icons/github.svg`
  returns `200 image/svg+xml`.
- **Reading:** all of that is **expected**. The org page listing no public
  repository is **not** a finding: Paulo shipped ahead of the public flip
  (W-058 to W-060). The **finding** is the link missing or without its
  `aria-label`, a different href, a check-22/24 href or glyph gone, or a
  non-`200` on the SVG. A `404` with the markup present means
  `static/icons/github.svg` was not in the image.
- **Retire:** the first sweep under the gate that sees the markup and the
  `200`.

### 35 — every `/static/` URL in a page carries `?v=<hash>`, cached for a year; unversioned ones revalidate (W-074, W-064) · RETIRED 2026-11-01, confirmed under `00070-r9n` (AUDIT_20261101T0758): 10 versioned URLs, 0 bare, `attendance.js` hash matches its body, both headers as stated

- **Gate:** the first serving revision created after W-074's merge into
  `master` (`deploy: immediate`; no SHA on the revision, per W-008).
- **Signature:** anon `GET /`: every `/static/` URL in the HTML ends in
  `?v=` plus 8 hex characters (ten on `base.html`: `main.css`, four
  favicon/manifest links, three footer icons, `attendance.js`, `nav.js`).
  For `js/attendance.js?v=X`, `X` equals the first 8 hex of `md5` of the
  body that URL returns. Response headers: a versioned URL →
  `cache-control: public, max-age=31536000, immutable`; the same path
  without `?v=` → `no-cache`; `/` itself → no `cache-control`. Under
  `00065-mzr` no `/static/` response carried `cache-control` at all.
- **Reading:** all of that is **expected**. The **finding** is a
  `/static/` URL in a page without `?v=`, a `v` that does not match the
  md5 of its body, a versioned URL without `immutable`, or a 500 on `/`
  (a file `static_url` names is missing from the image). A `beta.` host
  answering `301` with no `cache-control` is by design. A `?v=` that
  matches no file, answered as `immutable`, is W-075, not a regression.
  Whether the calendar popup opens can't be seen anon. Paulo confirms it,
  so don't report it either way.
- **Retire:** the first sweep under the gate that sees the ten versioned
  URLs, the matching hash and both headers.

### 36 — attendance can no longer be written on a finished edition (W-072) · RETIRED 2026-11-01, confirmed under `00070-r9n` (AUDIT_20261101T0758): 0 of 61 late rows, anon POST and DELETE `401`

- **Gate:** the first serving revision created after W-072's merge into
  `master` (`deploy: batched`; no SHA on the revision, per W-008).
- **Signature:** in `web.attendance` joined to `core.event_occurrences`
  on `occurrence_id`, count the rows with
  `coalesce(eo.end_date, eo.start_date) < a.created_at::date`. It reads
  **0**: 0 of 57 on 2026-10-30, after W-066's three accidental rows were
  deleted by hand. Before the gate, a click on a tile the day after its
  race could add one. Anon `POST` and `DELETE` on
  `/events/<id>/<occurrence_id>/attendance` still answer `401`.
- **Reading:** 0 and `401` are **confirmation**. The **finding** is a
  row created under the gate on an occurrence whose last day had already
  passed at `created_at`. Before calling it a regression, check whether
  the scraper moved that occurrence's dates earlier after the mark: that
  is a legitimate row, so note it and don't count it. A row created
  before the gate is pre-existing, not a regression.
- **Retire:** the first sweep under the gate that reads 0 and `401`.

### 37 — visibility has two levels: no `private` row, two radios, one CHECK (W-076) · RETIRED 2026-11-01, both steps confirmed (AUDIT_20261101T0758): two-value CHECK, `crews_only` 3, `public` 19, no `private` row; migration 014 has run

- **Gate:** two steps, confirm each on its own. (a) The first serving
  revision created after W-076's merge into `master` (`deploy:
  immediate`; no SHA on the revision, per W-008). (b) Paulo running
  `migrations/014_visibility_two_levels.sql` by hand, after (a). Tell
  them apart by the constraint: `SELECT pg_get_constraintdef(oid) FROM
  pg_constraint WHERE conname = 'users_visibility_check'` lists two
  values after (b), three before.
- **Signature:** `SELECT visibility, count(*) FROM web.users GROUP BY 1`.
  Before (b): some `private` rows, no `crews_only` (2026-10-31).
  After (b): no `private` row; the former `private` rows are
  `crews_only`; `public` unchanged unless someone saved. Anon `GET /settings` → 303 to sign-in, as
  before; the page itself can't be swept anon. Anon `GET /profile/<id>`
  for the formerly private users → the hidden placeholder, before and
  after, as for every anon profile request.
- **Reading:** under (a) alone, the `private` rows are **expected**,
  not a regression: that is the deploy gap the ticket planned. Under
  (b), zero `private` and the two-value CHECK are **confirmation**. The
  **finding** is a `private` row created after (a) (`updated_at` later
  than the revision), the three-value CHECK still in place a sweep
  after (b) was reported done, or a 500 on `/settings` or `/profile/*`.
  A `private` row surviving (b) with the two-value CHECK in place is
  impossible; if seen, the UPDATE and the ALTER did not run together.
- **Retire:** the first sweep that reads the two-value CHECK and no
  `private` row.

### 38 — the crew page is a hub: an agenda read on every member visit (W-077) · RETIRED 2026-11-01, confirmed under `00070-r9n` (AUDIT_20261101T0758): ~30 `200`s on `/crews/*`, anon `401`, no 5xx. The three untested branches never fired

- **Gate:** the first serving revision created after W-077's merge into
  `master` (`deploy: immediate`; no SHA on the revision, per W-008).
- **Signature:** `GET /crews/<slug>` now runs two more reads per member
  visit (members ⋈ `web.attendance` ⋈ `core.event_occurrences` with an
  `EXISTS` on the view, then the MV by event id) and renders an agenda
  beside Members and Invite. The page can't be swept anon: anon `GET
  /crews/<slug>` stays a bare `401`, as before the gate (W-085 changes
  that to a 303; until it merges, 401 is not a finding). What can be
  swept: the request log for `GET /crews/*` and its status codes.
- **Reading:** 200s and anon 401s on `/crews/*` are **confirmation**. The
  **finding** is any 5xx on `GET /crews/<slug>` under the gate: the
  branches nothing exercised before merge are an edition marked by a
  member that has left the view (rendered unlinked), a crew whose marks
  are all past (the empty state through the route), and a TBC occurrence
  whose `expected_month` is outside 1–12 (`date()` would raise). Quote
  the traceback and the slug; the occurrence ids follow from the slug's
  members' attendance.
- **Retire:** the first sweep under the gate with no 5xx on `/crews/*`.

### 39 — `GET /crews` exists: a 303 signed in, a 401 anon (W-078) · RETIRED 2026-11-01, confirmed under `00070-r9n` (AUDIT_20261101T0758): anon `401`, three `303`s, no 5xx on `/crews` or `/profile/*`

- **Gate:** the first serving revision created after W-078's merge into
  `master` (`deploy: immediate`; no SHA on the revision, per W-008).
- **Signature:** anon `curl -sI https://indierunners.co/crews` returns
  `401` where it returned `404` (no route matched a bare `/crews`). Signed
  in, the nav's Crews item is `GET /crews`, a `303` to `/crews/<slug>` or
  `/profile/<id>#crews`. `GET /profile/<id>` runs one more read when the
  viewer is the owner (crews with a member count). `/settings` renders no
  Crews section.
- **Reading:** anon `401` on `/crews`, and `303`s on `GET /crews` in the
  request log, are **confirmation**. The **finding** is a `404` on
  `/crews` under the gate (the revision doesn't carry W-078), a `200` or
  `5xx` on `GET /crews`, or any `5xx` on `GET /profile/*`. Once W-085
  merges, anon `/crews` becomes a `303` to sign-in, and that is not a
  finding either.
- **Retire:** the first sweep under the gate with anon `/crews` not `404`
  and no `5xx` on `/crews` or `/profile/*`.

### 40 — crew members mark races from the hub: `POST /crews/<slug>/attendance` (W-079) · RETIRED 2026-11-01, never exercised: W-079 was reverted (1.9.55, serving `00072-bcf`) and dropped by Paulo. Its gate was met by `00071-txg` for minutes with no traffic. Under `00072` and later the route is gone, so an anon POST answering `404` is expected, not a finding

- **Gate:** the first serving revision created after W-079's merge into
  `master` (`deploy: immediate`; no SHA on the revision, per W-008).
- **Signature:** a new route, `POST /crews/<slug>/attendance`, appears
  in the request log and answers `303` to `/crews/<slug>` (with
  `?view=going` when posted from that view). Every row on
  `GET /crews/<slug>` ends in a Going | Interested form. Anon `POST`
  answers `401`, and a non-member gets `404`. No new `web.*` shape.
  Rows written through it are ordinary `web.attendance` rows, so check
  36 already covers marks on finished editions.
- **Reading:** `303`s, anon `401`s and occasional `404`s are
  **confirmation**. The **finding** is a `400` on this route under the
  gate. The hub then offered a control the lock refused: either a row
  rendered before midnight and posted after, or a TBC occurrence with a
  past `start_date` (0 attended rows on 2026-11-01). The reader saw raw
  JSON (W-089). Quote the slug and time. Then list the crew's attended
  occurrences that have `status = 'tbc'` and a past `start_date`, with
  ids and dates. Any `5xx` on `/crews/*` is also a finding.
- **Retire:** the first sweep under the gate with `303`s on the route
  and no `400` or `5xx` on it. Before then, a sweep with no traffic on
  the route proves nothing. Note it and carry the check forward.

### 41 — `web.users.display_name` holds `Paulo M.`, not a full name (W-090, W-091) · RETIRED 2026-11-02, confirmed under `00076-ldv` (AUDIT_20261102T1131): `long` 0 of 34, six callbacks under (c) with no 5xx. Step (b) is read from the count, not yet from Paulo

- **Gate:** two steps, confirm each on its own. (a) The first serving
  revision created after W-090's merge into `master` (`deploy:
  immediate`; no SHA on the revision, per W-008). (b) Paulo running
  `migrations/015_display_name_short.sql` by hand, after (a). There is
  no schema marker for (b): read it from the signature's count dropping
  to 0, or from Paulo saying so. (c), added at W-091's review: the
  first serving revision created after W-091's merge (`deploy:
  immediate`). W-091's developer reports (b) ran on 2026-11-01, before
  (c); not yet confirmed by Paulo.
- **Signature:** read-only, counts only, **never select or quote a name**:
  `SELECT count(*) AS users, count(*) FILTER (WHERE btrim(display_name)
  ~ '\s' AND display_name !~ '\s\S\.$') AS long FROM web.users`. On
  2026-11-01, before (a): `long` was most of `users`. Request log: any
  `/auth/google/callback` under (a) followed by no 5xx.
- **Reading:** under (a) alone, `long` falling as users sign in is
  **expected**. After (b), `long` = 0 is **confirmation**. A short form
  with two given names (`Ana María G.`) ends in `\s\S\.` and is not
  counted, by design. The **finding** after (b) is `long` > 0. Take the
  `updated_at` of those rows only. Earlier than (a)'s revision means
  015 did not touch it. Between (b) and (c)'s revision is **expected
  residue**: an account with its whole name in the first-name field
  signed in before W-091 served. It clears at that account's next
  sign-in. Later than (c)'s revision is the **finding**: a regression.
  A 5xx on the callback under (a) or (c) is the urgent finding: sign-in
  is broken.
- **Retire:** the first sweep after (c) that reads `long` = 0, or only
  residue rows, and sees at least one callback under (c) with no 5xx.

### 42 — every POST and DELETE refuses a foreign `Origin` (W-031) · RETIRED 2026-11-02, confirmed under `00076-ldv` (AUDIT_20261102T1131): attendance `200` ×17, `/crews/join` `303`, one `403` from a curl with no `Referer`. The size discriminator below was wrong: 28 bytes is the body, and the log's `responseSize` counts headers (`137`), which vary, so no byte count is stable. From logs, a `403` on any listed route except rotate is the middleware. On rotate, logs cannot separate the two; the `Referer` settles only whether our own forms are refused

- **Gate:** the first serving revision created after W-031's merge into
  `master`. It is `deploy: batched`, so it ships with the next deploy
  from `master`, likely a crews ticket (`immediate`).
- **Signature:** the request log on POST/DELETE
  `/events/*/*/attendance` and POST `/settings`,
  `/settings/delete-account`, `/crews/new`, `/crews/*/invite/rotate` and
  `/crews/join/*`. Count `403`s against `2xx`/`3xx`. The middleware's
  `403` is a 28-byte plain-text body (live `content-length`; the log's
  `responseSize` adds headers). See the header for telling it apart.
- **Reading:** `303`s and `200`s from real browsers, with no 28-byte
  `403`, is **confirmation**: production `Host` matches the browser's
  `Origin`. A 28-byte `403` whose `Referer` is an `indierunners.co`
  page is the **urgent finding**. Our own forms are being refused, so
  attendance and settings are broken for everyone. Quote route, time
  and user agent. A 28-byte `403` with a foreign or missing `Referer`
  is the check working: note it, it is not a finding.
- **Retire:** the first sweep under the gate that sees at least one
  `2xx`/`3xx` POST on attendance and one on a form route (`/settings`
  or `/crews/*`), and no 28-byte `403` with an `indierunners.co`
  `Referer`. A sweep with no POST traffic proves nothing. Carry it.

### 43 — a Google callback without a `code` is a `303` to `/`, never a `422` (W-092) · RETIRED 2026-11-03 (AUDIT_20261103T0806): under `00078-dnh` one `303` with `error=access_denied` and no `422`. That one was a curl probe 29s after the revision came up, not a visitor, but it ran the same branch a cancel does. The callback's 5xx on a refused `code` is W-094, which gets its own check at review

- **Gate:** the first serving revision created after W-092's merge into
  `master` (`deploy: immediate`).
- **Signature:** request log, `GET /auth/google/callback`. Group by
  status and by the `error=` value in the URL. A completed sign-in
  answers `307`; a callback without a `code` answers `303`.
- **Reading:** `303` with `error=access_denied` is **confirmation**: a
  visitor cancelled and landed on the homepage. A `422` on the callback
  is the **finding**: the fix is not serving. A `303` with any other
  `error=` value is a **finding**: quote the value, time and user agent.
  Repeated, it is **urgent**: Google is refusing sign-ins, and the fix
  now hides that as a quiet return home. A `303` with neither `code`
  nor `error=` is a probe or a stale link: noise, note the count. A `5xx` on a callback with a
  `code` is a pre-existing exchange failure, not this check's; note it.
  No callback traffic proves nothing. Carry it.
- **Retire:** the first sweep under the gate with at least one `303`
  carrying `error=access_denied`, no `422`, and no other `error=` value.

### 44 — crew member rows link to `/profile/<id>` (W-080) · RETIRED 2026-11-03 (AUDIT_20261103T0806 F3, PM's log read). The gate and signature below were both wrong, and are corrected here. **Gate:** `00080-vml`, image `4bce16ab…`. `00079-8cf` was created after the merge but carries `00078`'s image. **Signature:** a crew-referred `GET /profile/<id>` with **no** `307 GET /profile` from the same Referer just before it. Before 1.9.60 every crew-referred profile view was the page's "← My profile" back link, which redirects to the viewer's own id. **Confirmed:** `2026-11-03T00:14:55Z 200 /profile/29`, Referer `/crews/<crew>`, no `307` before it, and 29 is not the viewer

- **Gate:** the first serving revision created after W-080's merge into
  `master` (`deploy: immediate`, changelog 1.9.60).
- **Signature:** request log, `GET /profile/<id>` whose `Referer` is
  `/crews/<slug>`. These are new: before 1.9.60 the crew page linked to
  no profile.
- **Reading:** crew-referred `200`s are **confirmation**. A `4xx` or
  `5xx` on a crew-referred profile GET is the **finding**: quote time,
  status and user agent. A `5xx` on `GET /crews/<slug>` under the gate is
  also a finding. A `200` cannot tell a profile from the hidden
  placeholder (both answer `200` by design), so read nothing about
  visibility from it. No crew-referred traffic proves nothing. Carry it.
- **Retire:** the first sweep under the gate with at least one
  crew-referred `200` and no `4xx` or `5xx` on those requests.

### 45 — a Google code the token endpoint refuses is a `303` or a `400`, never a `500` (W-094) · RETIRED 2026-11-04, confirmed under `00082-96x` (AUDIT_20261104T0705): one refusal, `invalid_grant`, answered `400`, no callback `500` in 24h. That refusal was our curl probe, signed out; the signed-in `303` replay branch has no live evidence. **Severity: none.** App stderr lines land as DEFAULT, so the brief's `severity>=ERROR` read sees request-log `5xx` and no app line at all, this one included. A refusal other than `invalid_grant` (sign-in broken for everyone) shows only as callback `400`s with no `307`s. Check 49 carries that read until W-051 adds the severity. The two sibling `500`s are W-105

- **Gate:** the first revision created after W-094's merge whose image
  digest is **not** `4bce16ab…`. `00080-vml` and `00081-5b9` both carry
  `4bce16ab…`, the image before W-094; a revision created later on that
  image (infra apply, config change) is not under the gate.
- **Signature:** request log, `GET /auth/google/callback` with a `code`:
  no `500`. A refused code answers `303` (session already signed in) or
  `400` (signed out). Each refusal writes one stderr line
  `Google refused the code exchange: <error>`, never the code itself.
- **Reading:** `invalid_grant` on a callback that follows a `307` for the
  same code within seconds is a replay handled: **confirmation**. A
  lone `400` with `invalid_grant` is a signed-out stale or bogus code:
  note it. **Urgent finding:** `invalid_client`, `unauthorized_client`
  or `redirect_uri_mismatch`, or several refusals with no `307` around
  them. That is sign-in broken for everyone (secret or OAuth config), and
  the fix now shows it as a 400 page, not a 500. A **number** as the
  value (`500`, `503`) is Google's token endpoint failing: note it. A
  `500` on a callback with a `code` is a **finding** unless its traceback
  is `httpx.RequestError` (Google unreachable) or comes from
  `get_userinfo`: those two are known and unfixed (DEV_NOTES
  2026-11-03), note them. A `500` from `exchange_code_for_token` means
  the fix is not serving. Record the **severity** Cloud Logging gives
  the refusal line; nobody has seen it. No callback refusals proves
  nothing. Carry it.
- **Retire:** the first sweep under the gate with at least one refusal
  line, its callback answered `303` or `400`, no `500` from
  `exchange_code_for_token`, and the severity recorded.

### 46 — the crew hub serves no Going-only filter, and `?view=going` is ignored (W-095) · RETIRED 2026-11-04, confirmed under `00083-ds8` (AUDIT_20261104T0705): hub `200` ×13 under `00085`, no `?view=going` in 24h

- **Gate:** the first revision created after W-095's merge whose image
  digest differs from the image serving at merge time. The developer's
  deploy output names it. A revision created later on the old image is
  not under the gate.
- **Signature:** request log, `GET /crews/<slug>`. The hub no longer
  links to `?view=going`, so a `GET /crews/<slug>?view=going` whose
  Referer is a hub page should not appear. One that does arrive (a
  bookmark, an old tab) answers `200`, the same as the plain URL.
- **Reading:** hub `200`s and no hub-referred `?view=going` is
  **confirmation**. A `?view=going` with no Referer, answered `200`, is a
  bookmark: note it. **Finding:** a hub-referred `?view=going` under the
  gate (the old template is serving), a `4xx` on `?view=going` (the
  parameter is being validated), or a `500` on `/crews/<slug>` (a
  `list_agenda` caller still passing the removed flag). Anon `401` on the
  hub is pre-existing and W-085's, not a finding here. The hint's
  removal is signed-in only and cannot be read from logs. No hub traffic
  proves nothing. Carry it.
- **Retire:** the first sweep under the gate with at least one hub
  `200` and no hub-referred `?view=going`.

### 47 — leaving a crew keeps every crew owned by a member admin (W-081) · RETIRED 2026-11-04, confirmed under `00084-nl6` (AUDIT_20261104T0705): leave `303` ×3, no `500`, the invariant query zero rows. The `Location` is inferred from the status; logs do not carry it

- **Gate:** the first revision created after W-081's merge whose image
  digest differs from the image serving at merge time. The developer's
  deploy output names it.
- **Signature:** request log, `POST /crews/<slug>/leave` answers `303`
  to `/profile/<id>?left=…#crews`. `404` is a non-member and `403` a
  cross-origin request, both by design. Then one read-only query, which
  should return zero rows:

  ```sql
  SELECT 'empty crew', c.id FROM web.crews c
   WHERE NOT EXISTS (SELECT 1 FROM web.crew_memberships m WHERE m.crew_id = c.id)
  UNION ALL
  SELECT 'crew owner not admin', c.id FROM web.crews c
   WHERE NOT EXISTS (SELECT 1 FROM web.crew_memberships m
     WHERE m.crew_id = c.id AND m.user_id = c.created_by AND m.role = 'admin')
  UNION ALL
  SELECT 'invite owner not admin', i.id FROM web.crew_invites i
   WHERE NOT EXISTS (SELECT 1 FROM web.crew_memberships m
     WHERE m.crew_id = i.crew_id AND m.user_id = i.created_by AND m.role = 'admin');
  ```

- **Reading:** leave `303`s and zero rows is **confirmation**. **Finding:**
  a `500` on the leave route, a `500` on `POST /settings/delete-account`
  (the soft-ref leftover check refused), or any row from the query. For a
  row, name the crew and say whether a leave or deletion touched it in
  the log window. An empty crew can also come from two members leaving at
  once, which the W-081 review accepted. No leave traffic proves nothing
  for the log half. Run the query anyway and carry the entry.
- **Retire:** the first sweep under the gate with at least one leave
  `303` and zero rows from the query.

### 48 — an admin's removal keeps every crew owned by a member admin (W-082) · RETIRED 2026-11-04, confirmed under `00085-s7w` (AUDIT_20261104T0705): remove `303` ×1, `?removed=1` rendered `200`, the invariant query zero rows

- **Gate:** the first revision created after W-082's merge whose image
  digest differs from the image serving at merge time. The developer's
  deploy output names it. It may be the same revision as check 47's.
- **Signature:** request log, `POST /crews/<slug>/members/<id>/remove`
  answers `303` to `/crews/<slug>?removed=1`. `403` is a non-admin, an
  admin on themself, or a cross-origin request. `404` is a non-member
  actor or target. All are by design. Then run check 47's invariant
  query. One run serves both checks, so run it for this one even after
  47 retires. It should return zero rows.
- **Reading:** remove `303`s and zero rows is **confirmation**. **Finding:**
  a `500` on the remove route, or any row from the query. For a row, name
  the crew and say whether a remove touched it in the log window. An
  empty crew can also come from two admins removing each other at once,
  which the W-082 review accepted. No remove traffic proves nothing for
  the log half.
- **Retire:** the first sweep under the gate with at least one remove
  `303` and zero rows from the query.

### 49 — sign-in broken for everyone shows only as callback `400`s, until app lines carry a severity (W-051) · LIVE — standing read until W-051 serves

- **Gate:** every sweep from `00086-nt2` onward. A standing read, not a
  shipped change: check 45's sweep found the refusal line carries no
  severity, so the brief's `severity>=ERROR` read never shows it.
- **Signature:** request and stderr logs, 24h:
  `textPayload:"Google refused the code exchange"`, each with its
  callback status, and the count of callback `307`s.
- **Reading:** no refusal, or `invalid_grant` only, with `307`s present:
  **confirmation**, one line. **Urgent finding:** any other error
  (`invalid_client`, `unauthorized_client`, `redirect_uri_mismatch`), or
  callback `400`s with no `307` in the window. That is the OAuth secret
  or config broken, and every visitor sees the sign-in-failed page. A
  number as the error is Google's endpoint failing: note it. No callback
  traffic proves nothing. Carry it.
- **Retire:** W-051 serving, with an app warning read at `WARNING`, and
  the auditor brief's error read widened to cover it. The PM hands the
  brief change to the chief of staff at W-051's review.

### 50 — attendance is marked from event pages only, never from the index (W-096) · RETIRED 2026-11-13, confirmed under `00089-wxs` onward (AUDIT_20261111T1224, AUDIT_20261113T0829): every attendance `POST`/`DELETE` in 7d a `200` with an event-page Referer, none from the index

- **Gate:** the first revision created after W-096's merge whose image
  digest differs from the image serving at merge time. The developer's
  deploy output names it.
- **Signature:** request log, `POST` and `DELETE` on
  `/events/<id>/<occurrence>/attendance`, grouped by Referer. Tiles
  render only on the index, so after the gate every such request has an
  event page (`/events/<slug>/<year>`) as its Referer, never `/` or
  `/?<filters>`.
- **Reading:** attendance `200`s, all event-page-referred:
  **confirmation**. An index-referred request within a few hours of the
  gate revision is a tab opened before the deploy: note it with its
  time. **Finding:** an index-referred request more than a day after the
  gate revision (the old template or a cached old script is serving), or
  a `5xx` on the attendance routes. No attendance traffic proves
  nothing. Carry it.
- **Retire:** the first sweep under the gate with at least one
  event-page-referred attendance `200` and no index-referred request
  more than a day after the gate revision.

### 51 — the profile's changed query answers `200`, never a `500` (W-098) · RETIRED 2026-11-05, confirmed under `00091-64p` and `00092-vzb` (AUDIT_20261105T0851): browser profile `200` ×5, no `5xx` on `/profile/*`. The one `422` (`/profile/27+`) is a malformed id, not the query: W-109

- **Gate:** the first revision created after W-098's merge whose image
  digest differs from the image serving at merge time. The developer's
  deploy output names it.
- **Signature:** request log, `GET /profile/<id>` and the nav's
  `GET /crews` `303` that lands there. The profile query now also reads
  `core.event_occurrences.expected_month` and the MV's `race_distance`,
  and builds month headings in Python.
- **Reading:** profile `200`s and no `5xx` is **confirmation**.
  **Finding:** any `500` on `/profile/<id>` under the gate. A missing
  `core.*` column or a NULL the month rule did not expect fails every
  profile that holds such a row, not just one. Anon `401`s on
  `/profile` are W-085's, not a finding here. No profile traffic proves
  nothing. Carry it.
- **Retire:** the first sweep under the gate with at least one profile
  `200` that is not one of our curl probes, and no `5xx` on the route.

### 52 — the index tile panel shows counts only, and the grid steps down at 899 and 649px (W-107) · RETIRED 2026-11-05, confirmed under `00092-vzb` (AUDIT_20261105T0851): 0 `hover-faces`, breakpoints 1100/899/649, `fitDistances` ×2. The one `500` on `/` was a dropped DB connection, check 55

- **Gate:** the first revision created after W-107's merge whose image
  digest differs from the image serving at merge time. The developer's
  deploy output names it.
- **Signature:** static, not in the request log. Before the gate
  (2026-11-04): `/` carries 80 `hover-faces`, the served `main.css`
  steps `.race-grid` at 780px and 480px, and `attendance.js` has no
  `fitDistances`. After it, all three flip:
  ```bash
  curl -s https://indierunners.co/ | grep -c hover-faces            # 0
  curl -s https://indierunners.co/static/css/main.css | grep -o 'max-width: [0-9]*px) *{ *\.race-grid'   # 1100, 899, 649
  curl -s https://indierunners.co/static/js/attendance.js | grep -c fitDistances   # >= 1
  ```
- **Reading:** zero `hover-faces`, breakpoints 1100/899/649, and
  `fitDistances` present is **confirmation**. **Finding:** any one of the
  old values under the gate (an old image, or a cached asset with the
  new `?v=` hash missing), or a `5xx` on `/`. A cut row on Gapa
  Everesting Festival at 1101 to 1129px is W-108's known defect, not a
  finding here.
- **Retire:** the first sweep under the gate where all three read the
  new values.

### 53 — the tile panel's +N undoes itself when it does not help, and the narrowest band is tighter (W-108) · RETIRED 2026-11-05, confirmed under `00092-vzb` (AUDIT_20261105T0851): 2, 1, 57. The layout was never in curl's reach; a cut row is now for a person to report, not a sweep

- **Gate:** the first revision created after W-108's merge whose image
  digest differs from the image serving at merge time. The developer's
  deploy output names it.
- **Signature:** static. Before the gate (2026-11-04) all three read the
  old values:
  ```bash
  curl -s https://indierunners.co/static/js/attendance.js | grep -c 'more.remove()'   # 1 -> 2
  curl -s https://indierunners.co/static/css/main.css | grep -c 'max-width: 1130px'   # 0 -> 1
  curl -s https://indierunners.co/ | grep -c 'hover-row-val--town'                   # 0 -> one per non-TBC tile
  ```
- **Reading:** 2, 1, and a non-zero count on `/` is **confirmation**.
  **Finding:** any old value under the gate, or a `5xx` on `/`. The layout
  itself is out of curl's reach. Under this gate, check 52's exemption for a
  cut row on Gapa no longer holds: a cut seen by anyone is a finding.
- **Retire:** the first sweep under the gate where all three read the new
  values.

### 54 — the header wordmark's "i" has an amber dot (W-103) · RETIRED 2026-11-05, confirmed under `00092-vzb` (AUDIT_20261105T0851): 1, 1, and "Indie Runners" in the stripped page

- **Gate:** the first revision created after W-103's merge whose image
  digest differs from the image serving at merge time. The developer's
  deploy output names it. W-103 is `deploy: batched`, so it may ride
  another ticket's deploy.
- **Signature:** static. Before the gate (2026-11-04) both read 0:
  ```bash
  curl -s https://indierunners.co/ | grep -c 'class="logo-i"'                  # 0 -> 1
  curl -s https://indierunners.co/static/css/main.css | grep -c '\.logo-i'    # 0 -> 1
  ```
- **Reading:** 1 and 1 is **confirmation**. **Finding:** either 0 under the
  gate, or `/` no longer containing the text "Indie Runners" in its nav once
  tags are stripped, or a `5xx` on `/`. The colour itself is out of curl's
  reach.
- **Retire:** the first sweep under the gate where both read 1.

### 55 — a DB connection dropped mid-request, each end seeing the other vanish · LIVE — standing read from `00092-vzb`

- **Gate:** every sweep from `00092-vzb` onward. Nothing shipped: the PM
  traced AUDIT_20261105T0851 F2 and this is what a repeat should be read
  against. One in 14 days so far (2026-10-22 to 2026-11-05).
- **Signature:** web stderr, 24h, `textPayload:"server closed the
  connection unexpectedly"`; for each, the `cloudsql_database` log in the
  same second. The traced one paired with a client EOF, and no Cloud SQL
  operation (only the daily `BACKUP_VOLUME`) sat near it:
  ```
  23:15:57.114Z  web  GET 500 /   (request start, 0.73s; last DB request on that instance 23:09:07Z)
  23:15:57.641Z  db   [836381] user=postgres LOG: unexpected EOF on client connection with an open transaction
  23:15:57.917Z  web  psycopg.OperationalError: consuming input failed: server closed the connection unexpectedly
  ```
  Each end saw the other vanish in the same second, so the drop was
  between them (Cloud Run's Cloud SQL connector), not Postgres and not
  the app. Not established: why the connector dropped it.
- **Reading:** none is **confirmation**, one line. One with the same
  pair and no other in 7 days: note it with both lines. **Finding, routed
  to infra** with both lines quoted: a second within 7 days of another,
  or any on a request with a browser user agent, not a scanner. A drop paired with a Cloud SQL
  operation or restart is that operation: note which. One with no DB
  line in that second has a different cause: report it as new. A cluster
  in one sweep is urgent.
- **Retire:** seven consecutive sweeps with none, or the first routed
  repeat, whichever comes first. A routed repeat becomes infra's.

### 56 — "← All events" on an event page keeps the filters from an index Referer (W-102) · RETIRED 2026-11-13, confirmed under gate `00093-ljw` (image `b60e7b03…`) and later images (AUDIT_20261111T1224, AUDIT_20261113T0829): `/?country=austria`, `/`, `/`

- **Gate:** the first revision serving CHANGELOG 1.9.71 (W-102 merged). The
  developer's deploy output names it. W-102 is `deploy: batched`, so it may
  ride another ticket's deploy.
- **Signature:** take any event URL from the index (`<ev>` below). Before
  the gate, all three read `href="/"`:
  ```bash
  B='href="[^"]*" class="back-link"'
  curl -s -H 'Referer: https://indierunners.co/?country=austria' https://indierunners.co<ev> | grep -o "$B"  # -> href="/?country=austria"
  curl -s https://indierunners.co<ev> | grep -o "$B"                                                         # -> href="/"
  curl -s -H 'Referer: https://evil.example/?country=austria' https://indierunners.co<ev> | grep -o "$B"     # -> href="/"
  ```
- **Reading:** `/?country=austria`, `/`, `/` is **confirmation**. **Finding:**
  the first reading `/` under the gate (the Host Cloud Run passes is not the
  Referer's host, so the feature is dead in production); the third reading
  anything but `/` (the link points off the index); or a `5xx` on any
  event page.
- **Retire:** the first sweep under the gate that reads all three as
  expected.


### 57 — `beta.indierunners.co` no longer resolves or reaches the app (W-018) · RETIRED 2026-11-13, two sweeps confirmed (AUDIT_20261111T1224, AUDIT_20261113T0829). The second read NXDOMAIN from the system resolver, not `@8.8.8.8`; the PM re-read it through `https://dns.google/resolve?name=beta.indierunners.co&type=CNAME` the same day: `Status` 3, NXDOMAIN

- **Gate:** no new image. The gate is infra `cd04912` applied (beta mapping
  destroyed) and the beta CNAME deleted, 2026-11-09 ~15:27Z. Every sweep
  from the next one on; the logs reading applies from 24h after that, so
  resolver caches have expired.
- **Signature:**
  ```bash
  dig +short beta.indierunners.co @8.8.8.8                            # -> empty (NXDOMAIN)
  gcloud beta run domain-mappings list --region europe-west1          # -> indierunners.co, www.indierunners.co only
  curl -sI https://www.indierunners.co/ | head -1                     # -> 301, location https://indierunners.co/
  ```
  and Cloud Run request logs, 24h, `httpRequest.requestUrl:"beta.indierunners.co"`
  → no rows.
- **Reading:** all four as above is **confirmation**. **Finding:** beta
  resolving to anything (urgent if it is a CNAME to `ghs.googlehosted.com`
  with no mapping listed: that is the dangling shape W-018 closed; route
  to infra); a beta mapping listed (drift against infra); a beta request
  in the app's log after the 24h; `www` not answering 301.
- **Retire:** two consecutive sweeps under the gate reading confirmation.

### 58 — a crawler follows the event pages' "sign in" link, ignoring robots.txt · LIVE — standing read from `00097-8bs`

- **Gate:** every sweep from `00097-8bs` onward. Nothing shipped: the PM
  dispositioned AUDIT_20261113T0829 F1 as no ticket, and this is how a
  repeat reads. `GET /auth/google` sets a session cookie and answers
  `307` to Google, with no DB read (`app/main.py`, `google_login`), so
  the crawl costs a request and nothing else. `robots.txt` already
  disallows `/auth/`.
- **Signature:** request log, 24h: `GET /auth/google` by status, its top
  sources by range (last octet dropped), and `/auth/google/callback`
  requests from the same ranges.
- **Reading:** `307`s from a few ranges with no callback from them is
  **confirmation**, one line. It is not a sign-in count: say so when
  check 49 reads callbacks. **Finding:** a `5xx` on `/auth/google`; a
  callback from a crawler range (it is completing Google's flow); the
  same ranges on `POST` routes or on `/crews/join/*`; or starts above
  2,000 in 24h.
- **Retire:** seven consecutive sweeps with no crawler starts, or an edge
  rule from infra that blocks them, whichever comes first.

### 59 — ARCHITECTURE's dated view counts are not a finding; the claims beside them are · LIVE — standing read from `00097-8bs`

- **Gate:** every sweep from `00097-8bs` onward. Nothing shipped:
  AUDIT_20261113T0829 F4 dispositioned as no ticket. W-002 re-measured
  the count once and it went stale again. `docs/ARCHITECTURE.md` dates
  it on purpose ("measurements with a shelf life [...] conclusions drawn
  from them are written to stand without them").
- **Signature:** the view, one query: events whose rows carry more than
  one distinct `occurrence_id`. The same section claims "Each event has
  exactly one live occurrence", and the grouping key rests on it.
- **Reading:** a dated count that differs from today's view is
  **confirmation**, not reported. Zero multi-occurrence events is
  **confirmation**, one line. **Finding:** any event with two live
  occurrences in the view (the tile and event page group on the event
  alone, so they would merge two editions), or a view count stated in
  ARCHITECTURE with no date.
- **Retire:** when a ticket changes how ARCHITECTURE states the grain.
