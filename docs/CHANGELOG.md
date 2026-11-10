# Changelog

All notable changes to the Indie Runners Web project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.9.76] — 2026-11-10

### Added — one script for an Unsplash round (W-104)

- **Wrong belief: a restart finishes a round.** The docs said "restart the
  app". Cost: on 2026-11-01 the new photos went live under the old stock
  photographers' credits. **New belief:** the restart reloads the
  dedicated slugs from GCS, but startup only writes credits for slugs in
  the manifest baked into the serving image, which predates the round
  (`event_image_service.py` `refresh_dedicated_attributions`; revision
  00086 redeployed 00085's digest 31 s before round 5's manifest commit).
  The backfill is what sets them.
- `scripts/unsplash_round.sh <file>` runs fetch (per line, interactive),
  manifest, publish, restart and backfill, stops naming the failing step,
  and warns on exit if the backfill did not run. The restart redeploys
  the serving revision's own image digest, after `deploy.sh --check` and
  a `y`. The four scripts it calls are unchanged.
- **Verified:** with stub `python` and `gcloud` on `PATH` (no production,
  no DB): comments and blank lines skipped, a multi-word query passed as
  one argument, the fetch's stdin is the terminal, not the list; a failing
  publish stops with "STOPPED at step: publish" and the backfill warning;
  declining the restart stops there with the same warning; the full path
  ends in the backfill. After the W-104 review (R1, R2): a last line with
  no newline is fetched; a missing file or directory, and a list of only
  comments, stop with exit 1 before any fetch, publish or restart. The real digest read
  (`status.imageDigest` of the serving revision) was run read-only
  against production. **Not yet run for a real round** (acceptance 5):
  Paulo runs it after W-115.

## [1.9.75] — 2026-11-09

### Changed — the image installs exact pinned versions (W-112)

- **Wrong belief: `requirements.txt` defined what production runs.** It
  set floors (only SQLAlchemy had a ceiling), so every `deploy.sh` build
  installed whatever was newest that day. Cost: the same commit built
  twice could differ, and with no test suite a regression couldn't be
  split into "our change" and "a dependency moved". **New belief:** the
  versions are part of the commit. `requirements.lock` is the `pip
  freeze` of the serving image, and the Dockerfile installs only it.
  `requirements.txt` stays as the direct dependencies.
- **Upgrading now:** edit `requirements.txt`, regenerate the lock with
  the command in its header, review the diff, deploy.
- **Verified:** froze revision 00094-862 by digest, built the branch
  image locally, and diffed the two sorted freezes: empty, 51 packages,
  both Python 3.11.18 (`evidence W-112`). Ran the local image against
  the DB: `/` renders tiles for anon and for a minted signed-in cookie
  (the signed-in render, not sign-in), and `/stats` renders. Nothing
  upgraded. The base tag still floats (out of scope).

## [1.9.74] — 2026-11-09

### Added — a git hook that refuses private terms (W-111)

- **Wrong belief: reading your own diff is enough to keep private names
  out of a public repo.** Cost: the pre-publication audit found crew
  slugs, user ids and a real name in tracked files, caught only by a
  one-off grep. Once pushed, a deleted commit still counts as published.
  **New belief:** a fixed list of known private terms should be checked
  on every commit, before the push. CI can't do that: it runs after the
  push, so `.githooks/` does it locally.
- **What it checks:** added lines of the staged diff and the commit
  message. Terms come from an untracked file in the main checkout's
  `exports/`, found from worktrees through `--git-common-dir`. With no
  term file it refuses. Seeded from the audit's must-be-zero list,
  without the surname that is in `LICENSE`. No seed term matches a
  `core.*` event or race slug (query and results in `evidence W-111`).
- **Verified** from the `irw-W111` worktree with throwaway commits on a
  local scratch branch, deleted afterwards and never pushed. Refused: a
  term in a file (mixed case, mid-line, reported as file and line), a
  term in the message only (also on a `#` line, which `-m` keeps), a term
  on a line after a `++ ` line, and any
  commit with the term file moved away. Passed: a clean commit, a commit
  removing a term line, an editor-mode commit, `commit -v` whose verbose
  diff showed a removed term, and `--no-verify`. From the main checkout,
  the term file resolves the same way. No `app/` code changed, so there is
  no page to check in either tier. Details in `evidence W-111`.

## [1.9.73] — 2026-11-09

### Removed — the beta host's sign-in callback and domain mapping (W-018)

- **Wrong belief: beta's traffic would reach zero once humans left**, so
  "no beta requests at all" was a usable gate for unmapping it. Cost: a
  gate that never opens, because scanners and crawlers never stop; it held
  a p4 open for weeks and was finally waived by hand. **New belief:** gate
  on the callback path and on human traffic, not on all requests.
  **Evidence:** the 30 days of request logs hold no beta callback hits
  (the same filter on apex finds live sign-ins), and beta's remaining
  traffic is scanners and crawlers. Beta's callback is off the OAuth
  client, its mapping gone (infra `cd04912`), its CNAME deleted last.
- **Verified:** after step 1, Paulo signed in on the apex in a browser and
  landed signed in (callback `307` at 15:15:24 UTC). After step 2, re-plan
  `No changes`; `domain-mappings list` shows apex and `www`; `curl` apex
  `200`, `www` `301` to apex. After step 3, beta is `NXDOMAIN` on three
  resolvers. No code change.

## [1.9.72] — 2026-11-09

### Changed — public-release audit, app/ (exports/public-audit-2026-11-09.md, H1, M2, L1)

- **Wrong belief: `/debug/health` was an internal route.** It needs no
  sign-in and returned `user_count` and `race_count`. Cost: anyone could read
  the user count, and the path is obvious once the code is public. **Now** it
  runs `SELECT 1` and returns `{"status": "ok"}`: still a database check for a
  post-deploy smoke test, with nothing about what the database holds. Nothing
  read the counts (no reference in this repo, infra or the scraper).
- **Wrong belief: sign-in log lines were harmless because `logger.info` is
  dropped (W-051).** They wrote the email (`user_service.py`, both branches)
  and the Google `sub` (`auth_service.py`). Dropped today, so nothing reached
  Cloud Logging, but fixing W-051 would have started logging both on every
  sign-in. **Now** they log the user id only.
- **Removed dead mockup files:** `app/templates/mockup_reference.html` (no
  route renders it), and `static/js/script.js` and `static/css/styles.css`,
  which only it loaded.
- **Verified:** `docker build`; the app imports inside the image. Not run
  through `scripts/dev.sh` (needs the database).

## [1.9.71] — 2026-11-08

### Fixed — "← All events" goes back to the filtered list the runner left (W-102)

- **Wrong belief: the event page's back link could be a plain `/`.** The
  filters are a `GET` form, so the filtered list has its own URL, but nothing
  carried it to the event page. Cost: every runner who filtered, opened an
  event and clicked back had to set their filters again.
- **New belief: the referrer already carries it.** `event_detail` copies the
  `Referer`'s query behind a literal `/?` when that referrer is this host's
  `/` with a query, and gives `/` otherwise. **Referrer, not a query
  parameter**: a parameter on the tile link would put filter state into every
  event URL people share or paste, and acceptance 3 wants those to give `/`.
  The referrer falls back to `/` in those cases (a URL pasted into a new tab,
  profile, crew hub, another site); a tile opened in a new tab from the
  filtered list still sends it, so that tab keeps the filters. It relies on no page setting a
  document-level `no-referrer` policy, the assumption `SameOriginMiddleware`
  already makes. Noted in both places.
- **What it does not cover.** Picking a race in the event page's table
  reloads the page, so the referrer becomes the event page and the link drops
  to `/` (a `shortcut:` in the code, and DEV_NOTES). Not a regression: it was
  `/` before. Also not exercised: the 302 from a finished year to the next
  (browsers keep the `Referer` across a redirect; not checked here).
- **Verified, served from this worktree (`/proc` cwd checked), both tiers
  (signed in = minted cookie: the render, not sign-in).** curl against
  `/events/achenseelauf/2027`, back-link `href` per `Referer`: none → `/`;
  `localhost:8000/?country=austria&distance_min=20&distance_max=60` → that
  query; `/profile` → `/`; `/` → `/`; `https://evil.example/?country=…` → `/`;
  `localhost:8000//evil.example/?x=1` → `/`; a `"><script>` query → escaped
  inside the `href`. Headless Chrome, scripted `.click()` on the tile and back link
  via CDP (two on the tile: headless reports `hover: none`): filtered index (45 tiles) → tile → back link lands on the
  same URL with Austria selected and the same 45 tiles; same event opened
  directly → `/`. The event page (and `base.html`) has no `rel="canonical"` or `og:` tags, so nothing there
  changes.

## [1.9.70] — 2026-11-04

### Fixed — the dot on the header's "i" is amber, like the brand mark (W-103)

- **Wrong belief: the wordmark was one colour because the brand is.** The mark
  in `static/brand/` has an amber dot; the header wordmark's was white. Cost: a
  mismatch on every page, for every visitor.
- **New belief: only the top of the letter needs colouring.** The "i" of "Indie"
  gets its own span, with a clipped gradient: amber above, white below. The
  cut-off is 0.48em from the top of the span's box, mid-gap: in Fraunces 700 the
  dot ends at 0.45em and the stem starts at 0.51em. Being in `em`, it scales with
  the font size. The header's font size is 22px at every width. Footer,
  `<title>` and `static/brand/` are untouched.
- **What that does not show.** The cut-off is measured on Fraunces only. If the
  font fails to load, the fallback serif's dot may not land on it, so part of the
  dot or stem could take the other colour. Text stays readable.
- **Verified, Chrome headless, served from this worktree (`/proc` cwd checked).**
  Anon at 1280px and 375px, and minted-cookie signed in (render, not sign-in) at
  the same widths: dot amber, stem white, checked by eye at 12x on anon 1280px and
  on the header shots at 2x. `textContent` and the link's accessibility-tree name
  read "Indie Runners". Wordmark width unchanged from production at 375px
  (152.1875px, both); at 1280px the box is set by the tagline, so that match says
  nothing. Footer and `<title>` read the same in both tiers. `/`, `/stats` and
  `/imprint` anon: 200, span present. Page search and copy-paste by hand: not
  tried; `textContent` is the evidence.

![Header at 1280px](screenshots/W-103-desktop.png)
![Header at 375px](screenshots/W-103-375.png)

## [1.9.69] — 2026-11-04

### Fixed — no swept tile loses a pill or its entry fee at the narrowest widths (W-108)

- **Wrong belief: when the panel overflows, the pills are why.** W-107's
  `fitDistances` added `+N` before it knew hiding helped. Cost, measured on
  production signed out: Gapa at 1101 to 1120px lost its second distance for
  nothing and the entry fee was cut 13 to 19px (1.9.68 said 14px), fully hidden
  at 1101px and 1110px, with no sign of it.
- **A second tile, which the ticket did not name.** Maraton San Sebastian on
  production at 1101 to 1110px: entry fee cut 18 to 21px. A two-line name, the
  registration badge and an interested line leave the rows 99px. So 1.9.68's
  "one tile of 456" is out of date. Whether that tile changed since W-107's
  sweep, or that sweep missed it, was not established.
- **New belief: hiding pills only stays if it made the rows fit.** Otherwise
  every pill comes back and `+N` goes. The location keeps to one line with an
  ellipsis and the full name in `title` (Paulo, 2026-11-04; five towns at
  1101px); there is no hover on touch, the event page has it. At 1101 to 1130px
  only, row gap is 3px and the divider margin 2px; other widths keep their
  spacing.
- **What that does not show.** The spacing was tuned until today's tiles fit;
  it is not a guarantee. `.hover-rows` still clips with no sign. At 1101px four
  tiles of 458 overhang by 0.4px, under the whole-pixel `scrollHeight` test the
  sweep used (no ink lost on Stuiben Trailrun's screenshot), and San Sebastian
  has 0.6px spare. A longer name or one more block
  cuts the entry fee again. The `shortcut:` at `.hover-rows` now says so.
- **Verified, Chrome headless, served from this worktree (`/proc` cwd
  checked), measuring `.hover-rows` and the panel's last child.** Anon over the
  month filters Nov 2026 to Dec 2027 (457 tiles) at 1100, 1101, 1105, 1110,
  1115, 1120, 1129, 1131, 1135, 1140, 900 and 650px: no row cut, last line
  inside, no empty `+N`, swept by whole-pixel `scrollHeight`. Minted-cookie signed in (render, not sign-in): `/` at
  1400, 1129, 1115, 1101, 900, 650, 375px, and the month filters at 1101px, same
  result. Gapa alone, 1101 to 1400px: both pills, entry fee inside. Screenshots
  of Gapa at 1110px and San Sebastian at 1101px checked by eye, panel revealed
  by class because the headless hover did not fire. Forced overflow by an
  injected 500px row: one pill leaves no `+N`, two pills both stay.

## [1.9.68] — 2026-11-04

### Fixed — the tile panel's last line is never cut off (W-107)

- **Wrong belief: only crowded tiles overflow, and distances are what grow.**
  The spec's premise, read from source. Cost, measured in Chrome on master
  across the 60 tiles of `/`: "Sign in to join →" fell off 29 tiles at 1101px,
  58 at 781px and 58 at 481px. Attendee faces took more height than the pills.
- **The spec's default was not enough, so Paulo chose (2026-11-04).** Pinning
  the last line and collapsing pills into `+N` held the line, but cut the rows
  on 60 of 60 tiles at 481px, some down to 0px high. Paulo's call: no faces in
  the panel, counts stay; four columns stay; only the lower switch points move.
- **New belief: a panel fits only on a tile about 260px wide or more.** The
  grid now goes to 2 columns at 899px (was 780) and 1 column at 649px (was
  480). This enlarges the tile's front face at those widths, which the spec
  had out of scope; Paulo approved it. `.hover-rows` shrinks while the
  attendee blocks and last line keep their height. `fitDistances` in
  `attendance.js` hides the pills that do not fit and adds `+N`, on load, on
  fonts ready and on grid resize. Without JS the rows clip with no `+N`.
- **Verified, Chrome headless, served from this worktree (`/proc` cwd
  checked).** `/` at 1400, 1200, 1101, 1100, 900, 899, 650, 649, 480 and
  375px, anon and minted-cookie signed in (hover render, not sign-in): last
  line inside the tile on every tile, no row cut. Anon at 1101, 900 and 650px
  over month filters Nov 2026 to Dec 2027 (456 tiles, past the 60 cap): last
  line inside on all; one row cut, below. Tap emulation at 375, 700, 1000px on
  Hochkoenig Ultraks: first tap reveals without navigating, last line inside,
  sign-in link reaches `/auth/google` (stubbed, Google not contacted), second
  tap opens the event. Desktop click opens the event. Resizing 1400 to 1101px
  refits `+N`.
- **Test tiles.** Most distances: Hochkoenig Ultraks (11). Going and
  interested: Transgrancanaria, signed in. Little content: Spreewaldmarathon,
  unchanged apart from its faces. Before and after screenshots at 1400, 1101,
  781 and 375px went to Paulo; they are not in the repo.
- **Known limit.** Gapa Everesting Festival, signed out at 1101 to about
  1129px: "Garmisch-Partenkirchen" wraps and the entry fee row is cut by 14px.
  One tile of 456; marked with a `shortcut:` comment and in DEV_NOTES.

## [1.9.67] — 2026-11-04

### Changed — the profile's race lists use the crew hub's calendar format (W-098)

- **Wrong belief: a profile list and a crew agenda are different things.**
  Paulo (IDEAS 2026-11-02): one format. Cost: the same race read two ways —
  month headings, a left day + weekday block and location · distances on
  the hub; a flat list with the date on the right, location only, and TBC
  rows dumped at the end on the profile.
- **New belief: the profile row is the hub's row.** `profile.html`'s macro
  now emits the hub's markup (`crew-agenda-row`, the day + `%a` block, the
  hub's sub-line expression) with the Going / Interested / Been there flag
  and the terrain badge in the chips slot, and prints a `crew-month` heading
  when the month changes (`loop.changed`). "Been there" stays its own
  section, newest month first. `ProfileRow` gains `expected_month` and
  `distances` (the attended edition's MV rows, else the event's, the same
  fallback as location); `TimelineRow` gains `month`: the date's month, else
  a TBC edition's expected month (December if unknown), the hub's rule. The
  upcoming sort is month, then the hub's order inside a month (dated rows by
  date, TBC last). **One decision beyond the format:** `race_date` is now
  `COALESCE(a.race_date, o.start_date)`. The snapshot is NULL when the date
  was unknown at mark time; five rows today (event 2959 for users 13, 15,
  26, 27; event 64 for user 31) have since gained a date, and the hub shows
  it. Dated snapshots are untouched, so W-084's split question is not; a NULL snapshot whose edition has since dated into the past would now file under Been there, as the hub files it (none today). The
  old `profile-race-row` grid and its phone rules had no other user and are
  deleted; the hub's classes carry the layout.
- **Not changed, named:** a TBC row whose expected month has passed stays in
  the upcoming list on the profile (NULL date = forward-looking) while the
  hub drops it; none exists today. No attendance row lacks an occurrence, so
  the "Date TBC" heading for a month-less row is unreachable today.
- **Verified** from this worktree (`/proc/<pid>/cwd` → `irw-W098`), signed
  in as user 13 on four profiles (own; 14 public; 31 crews-only, shared
  crew; 15 with a TBC row), the same pages captured from master first: the
  (name, flag) multiset of each section is identical before and after. User
  13 lands on 9 months plus 4 past, TBC rows under March 2027 and August
  2027, Comrades under June 2027 as "13 Sun" — the same month and day the
  captured crew hub shows. Sub-lines read e.g. "San Sebastián · 10 km,
  42.2 km". Anon `/profile/13` differs from master only in the stylesheet's
  content hash. Headless Chrome at 375px and 1280px: headings, the left date
  block, chips under the sub-line; the long Transgrancanaria sub-line wraps
  cleanly on the phone width. Not exercised: Google sign-in, a real phone.
  No migration.

## [1.9.66] — 2026-11-04

### Removed — the tile's Going / Interested / Change / Remove controls (W-096)

- **Wrong belief: a tile is a place to mark a race.** Paulo (IDEAS
  2026-11-02): the event page should be the only one. Cost: two surfaces
  with the same controls, one of them a hover panel whose bottom is already
  cut off on crowded tiles (IDEAS 2026-11-04).
- **New belief: a tile reports, the event page acts.** `race_tile.html`
  keeps the anon "Sign in to join →" and, on a tile the viewer has marked,
  the read-only "You are going" / "You are interested" line (Paulo,
  2026-11-03); the Change / Remove pair and the Going / Interested branch are
  gone. With that, no tile carries a `data-action`, so the "tile-only
  branch" of `attendance.js` turned out to be most of the file: the two
  avatar builders, the interested-strip maintenance, the count and
  hover-face refresh, the `tile--mine` toggle and the hover-cta markup were
  all reachable only from a tile click. Removed as one unit; the event-page
  path (`updateActionBar`, was `updateTile`) builds the same markup as
  before. The mobile reveal handler stays; only its now-dead
  `[data-action]` exemption went. `.hover-cta--going` / `--interested` had no
  other user and are deleted; `.attendance-buttons` stays for the action bar.
- **Verified** from this worktree (`/proc/<pid>/cwd` → `irw-W096`). Tiles:
  `/` anon and as user 13, served by this branch on :8000 and by master on
  :8001 from the main checkout, same cookies. Anon: identical (60 tiles, 60
  sign-in links, 80 attendee strips, 70 strip avatars, 0 `data-action`).
  User 13: the only differences are `data-action` in tiles 120 → 0 and
  Change / Remove 9 → 0; the 9 "You are interested" labels, 9 `tile--mine`,
  strips and avatars are identical; as user 20, 5 "You are going" labels and
  no control. Event page: headless Chrome driven over
  the DevTools protocol with user 1's cookie on an unlocked event — Going
  → "You are going" with the calendar dialog open and Change / Remove
  offered; Change → "You are interested"; Remove → the Going / Interested
  pair back. User 1 has 0 attendance rows before and after. Not exercised:
  a real phone's tap-to-reveal, Google sign-in. No migration.

## [1.9.65] — 2026-11-04

### Fixed — the Crews jump lands below the header; the empty calendar gets the crews box (W-101)

- **Wrong belief: `/crews` lands a no-crew runner on the My crews section.**
  It lands on the anchor, and the nav is 68px and sticky with nothing
  offsetting a fragment jump, so the section head — "My crews" and "Create a
  crew" — scrolled under it. Cost: Paulo's first-time runner saw only the
  empty box telling them to create a crew, and had to scroll up to find the
  button. The spec's mechanism, read from source, holds: measured in headless
  Chrome on a no-crew profile with races below the section, the head's top
  landed at viewport y=0 (its 37px fully under the nav) at both 375px and
  1280px, 725px tall. On a profile with nothing below the section the page
  was too short to scroll that far at that height, so the head stayed
  visible; a shorter phone viewport scrolls further. The sure case is a
  no-crew runner who already has races.
- **New belief: the page, not the section, declares the header's height to
  the scroll.** One rule, `html { scroll-padding-top: calc(68px + 1rem) }`,
  beside the nav rule in `main.css`. After it the head's top lands at 84px at
  both widths, 16px below the nav, with the button in the head as before.
  The leave flash uses the same anchor and so lands the same way. The rule is
  sitewide on purpose: the sticky nav is the cause, nothing in `static/js/`
  scrolls, and the only other in-page anchor (`href="#"` on the calendar
  dialog) is JS-handled.
- **The calendar's empty text sits in the `crews-empty` box**, own and
  someone else's; the own one keeps its second line as `crews-empty-sub`.
  `.profile-empty` had no other user and is deleted.
- **Verified** from this worktree (`/proc/<pid>/cwd` → `irw-W101`), signed-in
  render with minted cookies: user 1 (no crews, no races) shows both boxes
  and the flash with `?left=`; user 1 viewing user 29 shows the other-person
  box; user 13 (3 crews, 15 races) renders with no empty box. Anon
  `/profile/1` and `/profile/13` answer 200 as before. The landing was
  measured by saving the served HTML, pointing it at master's CSS and this
  branch's, and reading `scrollY` and the head's rect after re-triggering the
  fragment in headless Chrome with smooth scrolling turned off for the
  measurement (the end position is the same; the animation does not settle
  under a virtual-time budget). Not exercised: a real phone, Google sign-in.
  No migration.

## [1.9.64] — 2026-11-03

### Added — a crew admin can remove a member (W-082)

- **Wrong belief: an admin's only power is the invite link.** Roles existed
  (`crew_memberships.role`) but the only admin-gated action was rotate, and
  nothing removed another member. Cost: Paulo's decision 2 of Crews v1 ("the
  admin/creator is just one more member that is able to remove others")
  could not be followed; an unwanted member stayed until they chose to leave.
- **New belief: removal is a leave done by an admin, through the same
  hand-over.** `POST /crews/{slug}/members/{user_id}/remove` is gated in the
  order of the other crew POSTs: unknown slug or actor not a member → 404,
  actor not admin → 403, target is the actor → 403 (that is leave), target
  not a member → 404. Origin is W-031's middleware, no inline check. It calls
  `CrewService.remove_member`, so a removed creator hands `created_by` over
  exactly as a leaving one does, and the actor stays, so the crew never
  deletes on this path. 303 to `?removed=1`: the flash says the person can
  rejoin with the current link and carries a Rotate form, because nothing
  records a removal and invites have no expiry (Paulo: no auto-rotate, no
  notice). The sidebar shows Remove on every row but the admin's own, with an
  inline confirm and an `aria-label` naming the member. `?removed=1` carries
  no name, so W-081's arbitrary-flash-text shortcut is not repeated.
- **Verified** from this worktree (`/proc/<pid>/cwd` → `irw-W082`) with
  minted cookies on three throwaway users in one throwaway crew, the second
  admin set by an `UPDATE` on that row (test data, not a migration), all
  deleted afterwards through `delete_account` (0 users, crews, invites left).
  The creator's hub shows Remove on the two other rows and none on its own;
  the plain member's hub shows none. Anon POST `401`; `Origin:
  https://evil.example` `403`; plain member `403`; admin on themself `403`;
  unknown target `404`; made-up slug `404`. The second admin removed the
  member: `303` to the hub, flash with the Rotate form, the removed member's
  hub renders `crews_hidden.html` and their POST is `404`. The second admin
  then removed the creator: `created_by` on the crew and its live invite
  moved to the second admin, who is the only row left. Not exercised: the
  browser `confirm()` dialog. No migration.

## [1.9.63] — 2026-11-03

### Added — a member can leave a crew (W-081)

- **Wrong belief: joining a crew is enough; nobody needs to leave one.**
  `CrewService` had `add_member` and nothing that removes one, so the only
  way out was deleting the account. Cost: Crews v1 rule 5 ("if someone does
  not want a crew to see their plans, they leave the crew") could not be
  followed, and W-022's trap stood: any leave route that did not hand over
  `created_by` would leave a soft ref behind and 500 the next account
  deletion.
- **New belief: one hand-over, two callers.** `CrewService.remove_member`
  deletes the membership, then either deletes the crew (no one left) or
  promotes the longest-standing remaining member, admins first, and moves
  `created_by` on the crew and its invites to them; it does not commit.
  `delete_account` loops over it, so leaving and deleting agree by
  construction. `POST /crews/{slug}/leave` is gated like rotate (unknown
  slug or non-member → 404), Origin-checked by W-031's middleware with no
  inline check, and 303s to `/profile/{id}?left=<name>#crews`, where the
  own profile's My crews section flashes the name. The hub sidebar's Leave
  button confirms inline; with one member the text says the crew is deleted.
  A crafted `?left=` on your own profile shows arbitrary text in that flash;
  autoescaped, so accepted.
- **Verified** from this worktree (`/proc/<pid>/cwd` → `irw-W081`) on four
  throwaway users and four throwaway crews, all deleted afterwards through
  `delete_account` (0 users, crews or invites left). Minted cookies: the
  only-member and plain-member confirm texts render; anon POST `401`;
  non-member POST `404`; `Origin: https://evil.example` `403`. The four
  leaves each `303` to the profile with the crew name, and the DB after each
  matched the rule: plain member gone, `created_by` unchanged; creator out
  with an admin left, `created_by` → that admin; creator out as only admin,
  the first-joined member is now admin and owns the crew and its invite; only
  member out, crew gone. Then the creator's `POST /settings/delete-account`
  with `confirm=delete`: `303`, the one crew they were still in handed over.
  A `crews_only` leaver's profile read for the former crew-mate before the
  leave and rendered `profile_hidden.html` after. Not exercised: the browser
  `confirm()` dialog itself. No migration.

## [1.9.62] — 2026-11-03

### Removed — the crew hub's Going-only filter and small-crew hint (W-095)

- **Wrong belief: the hub needs a filter to separate commitment from
  curiosity, and a small crew needs telling that its count identifies people.**
  The filter was Paulo's own Crews v1 spec item (IDEAS: "Toggle: 'Going only'
  / 'Going and interested'"), built by W-077. The hint is older, a design
  choice shipped in phase 3 PR3 (`f777c87`, 2026-07-17). Once the hub was in
  use Paulo judged both unneeded, 2026-11-02, on the hint: "Remove that
  please"; on the filter: "that can go". Cost: a control and a caution on
  every hub visit, the caution one a small crew cannot act on.
- **New belief: the hub shows every row with both kinds of member, always.**
  The filter links, the `view` parameter, `list_agenda`'s `going_only` flag
  and its row skip, the three template branches on it, the hint and its
  `member_count` are gone, with their CSS (`.crew-view*`, `.crew-small-hint`,
  used nowhere else). `?view=going` is now an unknown query parameter, which
  FastAPI ignores. The leak the hint described is unchanged; ARCHITECTURE
  keeps its reasoning and records the removal.
- **Verified** from this worktree (`/proc/<pid>/cwd` → `irw-W095`), minted
  `{user_id: 13}`, a member of two crews under 4: `/crews/<crew-a>`
  (3 members) and `/crews/<crew-b>` (1): `200`, zero matches for
  `crew-view`, `Going only`, `Small crews`; legend carries both `Going` and
  `Interested` chips; rows carry interested names. `?view=going` on the first
  returns a byte-identical body. Anon `/crews/x`: `401` from
  `get_required_user`, untouched. The empty state was not exercised (no
  crew without marked races); its text is now the one literal. No migration.

## [1.9.61] — 2026-11-03

### Fixed — a replayed Google code is no longer a 500 (W-094)

- **Wrong belief: once Google sends a `code`, the token exchange succeeds.** A
  code is one-time: a reload, back button or double tap after a sign-in that
  worked replays it, Google answers 400 `invalid_grant`, and
  `response.raise_for_status()` escaped as a 500. Cost: three such 500s on
  2026-11-02 within seven seconds of a successful `307`, the only ERROR
  entries in 24h, each shown to a visitor who had just signed in. Quieter
  cost: a bad client secret would have looked the same, with no line naming
  Google's reason.
- **New belief: a refused exchange is a sign-in state, not a server fault.**
  `exchange_code_for_token` logs one WARNING with Google's `error` value
  (never the code) and raises `CodeExchangeRefused`. The callback reads the
  session: `user_id` present means the earlier sign-in worked, so `303` to the
  queued redirect or `/`, the W-092 status for "did not complete". Absent
  means the visitor is really signed out, so a `400` page says sign-in didn't
  complete and offers Try again; the queued `post_login_redirect` is kept,
  unlike W-092's cancel, so the retry still lands where they were going. Session
  key rather than a DB lookup: a deleted user's stale cookie goes to `/` and
  renders anon, which is the right outcome. `400`, not `401`: the code is bad,
  mirroring the `ValueError → 400` branch beside it. Locally the WARNING
  reaches stderr through Python's last-resort handler (nothing configures
  logging, W-051); what severity Cloud Logging gives it was not checked from
  here, so the routed check should grep `Google refused the code exchange`
  and record the severity it finds.
- **Verified** from this worktree (`/proc/<pid>/cwd` → `irw-W094`), against
  the real token endpoint. Anon `?code=bogus` and `HEAD`: `400`, body carries
  "Sign-in didn't complete" and `<a href="/auth/google">Try again</a>`. Minted
  `{user_id: 1}`: `303 /`, and `/me` with the same cookie still answers user 1;
  with `post_login_redirect: /settings` queued: `303 /settings`, returned
  cookie decodes to `{'user_id': 1}`. Anon with only the redirect queued: no
  `set-cookie`, so it stays queued. Five requests, five stderr lines
  `Google refused the code exchange: invalid_grant`; `bogus` appears only in
  uvicorn's access log (the URL, pre-existing and the same in production).
  `?error=access_denied` still `303 /` (W-092 untouched). Real sign-in: Paulo
  signed in against this worktree's server, callback `307`, `/` rendered signed
  in. His back button re-entered `/auth/google` instead of re-sending the
  callback URL, so a real code was not replayed; the bogus-code runs above are
  the replay evidence (same endpoint, same `invalid_grant`). No migration.

## [1.9.60] — 2026-11-02

### Changed — crew members link to their profiles; the invite box says how to use it (W-080)

- **Wrong belief: the Members list is a roster, so plain text is enough.** A
  crew-mate who wants to know who a member is has no path from the hub to that
  person's profile, although W-076 made every member's profile visible to every
  crew-mate (W-042's "private members stay plain text" rule lapsed with it).
  The invite help text warned about the link without saying what to do with
  it. Cost: the hub's one list of people led nowhere, and the invite box read
  as a caution rather than an instruction.
- **New belief: each member row is one link, avatar and name together,** to
  `/profile/<id>`, your own row included; the Admin tag stays outside the
  link. The avatar's `alt` is now empty because the name beside it is the
  link text. The help text says the spec's sentence (share it in your group
  chat; whoever opens it and signs in joins) and keeps a no-expiry warning.
  The per-member "Next: {race}" line from the original spec is not built:
  Paulo dropped it 2026-11-02.
- **Verified** from this worktree (`/proc/<pid>/cwd` → `irw-W080`), signed-in
  tier with a minted cookie for a member of a 16-member crew: all 16 rows
  render as `<a class="crew-member-link" href="/profile/<id>">`, and each of
  those 16 profile URLs returns 200 for that viewer. Anon `GET /crews/<slug>`
  still answers 401 JSON, unchanged (W-085). Minted cookie, not a real
  sign-in. No migration.

## [1.9.59] — 2026-11-02

### Fixed — cancelling Google sign-in lands on the homepage, not a JSON 422 (W-092)

- **Wrong belief: Google always returns a `code` to the callback.** It does not:
  Cancel on the consent screen redirects back with `error=access_denied` and no
  `code`, and the handler declared `code: str`, so FastAPI answered its JSON 422
  before any of our code ran. Cost: three mobile visitors on 2026-11-01 reached a
  raw error page at the moment they were deciding whether to join. A second,
  quieter cost: an invite landing queues `post_login_redirect` before the bounce
  to Google, and a cancel left it in the cookie, so a later unrelated sign-in
  would land on a stale invite.
- **New belief: a callback without a `code` is a sign-in that did not complete,**
  a cancel (`access_denied`) or an error Google reports; all of them go home,
  and none is assumed to be a cancel. `code` is optional;
  without it the handler pops `post_login_redirect` and answers `303 /`, the
  code base's existing status for this redirect. `/` rather than back to the
  invite or `/settings`, which would bounce an anonymous visitor straight to
  Google again. A signed-in session is untouched: `user_id` stays. No message
  about the cancel: the app has no flash mechanism (out of scope per spec).
- **Verified** from this worktree (`/proc/<pid>/cwd` → `irw-W092`). Anon:
  `?error=access_denied`, no query, and `HEAD` all `303` with `location: /`,
  never 422. Session pop: a minted cookie holding only `post_login_redirect`
  came back as Starlette's clearing cookie (`session=null; expires=1970`).
  Signed-in tier: minted cookie `{user_id: 1, post_login_redirect: …}` → `303 /`,
  returned cookie decodes to `{'user_id': 1}`, and `/me` with it still answers
  user 1. Anon `/` renders. A bogus `code` still reaches the token exchange
  (500 from Google's 400, pre-existing, out of scope). Real Cancel on Google's
  consent screen: Paulo clicked it against this worktree's server, landed on
  the homepage signed out.
  No migration.

## [1.9.58] — 2026-11-01

### Fixed — every state-changing request now checks it came from this host (W-031)

- **Wrong belief (W-022's): only the irreversible POST is worth guarding.** The
  session cookie is `samesite=lax`, which blocks other sites but trusts every
  `*.indierunners.co` host, and only `/settings/delete-account` checked `Origin`.
  Cost: a page on a sibling host (a hijacked `beta.` CNAME, W-018) could mark a
  signed-in runner as attending, change their visibility, create or join a crew,
  rotate an invite, or sign them out, all without them knowing.
- **New belief: the rule belongs to the method, not the route.** One
  `SameOriginMiddleware` refuses any non-GET/HEAD/OPTIONS request whose `Origin`
  host differs from `Host`; the inline check in delete-account is gone, and
  W-081/W-082's routes are covered before they exist. A missing `Origin` passes:
  a browser sends it on every POST and DELETE, so a sibling page cannot omit it,
  and a non-browser client already holds the cookie; keeping it lenient also keeps
  the brief's curl recipe working. Accepted gap: an extension or proxy that strips
  `Origin` in the victim's own browser would let a sibling request through.
  `GET /auth/logout` stays GET: a forced logout is a nuisance, not a loss, and a
  POST would turn the nav link into a form.
- **Verified** from this worktree (`/proc/<pid>/cwd` → `irw-W031`), minted cookie for
  user 1, every state-changing route: `Origin: http://beta.localhost:8000` → 403 on
  attendance POST and DELETE, settings, delete-account, crews/new, invite/rotate,
  join, and on an anon POST; `Origin: null` → 403. Same-origin: attendance POST
  wrote `going` and DELETE cleared it (DB checked before and after, empty both
  times); settings re-saved the current visibility (303); delete-account with
  `confirm=nope` → 400, never `delete`; crews/new with `!!!` → 400, rotate and join
  on a bogus slug/token → 404, all past the check. No `Origin` passes (200). Anon `/`
  and signed-in `/settings` render. Not verified: a real browser form submit, which
  sends `Origin` the same way curl did here only while no page sets a document-level
  `no-referrer` policy; under one, forms send `Origin: null` and get 403. No migration.

## [1.9.57] — 2026-11-01

### Fixed — a first-name field holding the whole name is shortened too (W-091)

- **Wrong belief (the PM's, in W-090's spec): a given name is one name**, so "no
  `family_name` → `given_name` alone" was safe. A Google account whose owner typed
  their whole name into the first-name box and left the last name empty sends exactly
  that, and `short_display_name` returned it unchanged: `{'given_name': 'Paulo
  Morales'}` → `Paulo Morales`, on every sign-in. Cost: W-090's goal fails for that
  account shape on every signed-in surface, and `web.users` cannot say how many there are.
- **New belief: `given_name` + `family_name` initial only when both are present;**
  otherwise the first-and-last-token rule runs over `given_name`, and over `name` only
  when `given_name` is empty. `Paulo Morales` → `Paulo M.`; `Paulo` → `Paulo`;
  `Ana María` + `García López` stays `Ana María G.` (the case splitting `given_name`
  unconditionally would break, now an assert). Seven asserts under `__main__`.
  Migration 015 is left as it is: Paulo ran it before this merged, so its "can be
  re-run" header is moot; the ticket's note that a re-run shortens `Ana María G.` to
  `Ana G.` stands as a record, not a fix.
- **Verified** from this worktree: `python3 -m app.services.user_service` prints `ok`.
  `dev.sh` served from `irw-W091` (`/proc/<pid>/cwd`); anon `/` is 200 with content, and
  `/profile` with a minted cookie for user 12 redirects to `/profile/12` and renders the
  stored name in `<title>` and `h1`; anon `/profile/12` is the private placeholder. The new output itself is not provable by
  a render: it is written only by a real Google sign-in, which needs a browser. Deploy
  carries no migration.

## [1.9.56] — 2026-11-01

### Changed — a runner is named `Paulo M.`, not by their full Google name (W-090)

- **Wrong belief: `display_name` is whatever Google's `name` says.** `user_service.py`
  wrote the full name on first sign-in and again on every later one, and every surface
  (nav initial, profile `<title>` and `h1`, Who's coming, the crew hub, `/me`) rendered
  that column. Cost: first and last name on every signed-in page, which Paulo called
  "imperative" to stop (IDEAS 2026-11-01).
- **New belief: the column holds the short form.** One helper, `short_display_name`,
  builds `given_name` + last initial + `.` (no `family_name` → given name alone; no
  `given_name` → the same rule on `name`'s first and last tokens; one token as is;
  nothing → NULL, rendered `Runner`), called at both write sites. Its five cases are
  asserts under `__main__` (`python3 -m app.services.user_service` prints `ok`).
  Migration 015 rewrites the stored rows the same way, only where there is more than
  one token and the row is not already `X Y.`, so it is a no-op on re-run and leaves
  `updated_at` (last sign-in) alone. Templates are unchanged: they already render the
  column verbatim.
- **Verified** from this worktree (`/proc/<pid>/cwd`), signed in as user 12 with a minted
  cookie: nav initial, `/profile` (`<title>` and `h1`), Who's coming on a 2026 event and
  the crew hub all show `display_name` as stored. Anon: that event page lists no names
  and `/profile/12` is the private placeholder. The short form itself is not provable by
  a cookie render: it is written only by a real Google sign-in or by 015. Evidence instead:
  the asserts, and 015's expression previewed read-only on six literals against the
  helper's `name` rule — identical on every row the WHERE touches, including
  `Anne-Marie de Wit` → `Anne-Marie W.`; against `web.users` the WHERE selects every multiword
  row, the PM's count. Three-token rows take the last token, as the spec
  accepts. Deploy the code, then Paulo runs 015; the other order writes full names back.

## [1.9.55] — 2026-11-01

### Reverted — the hub's Going | Interested control (W-079, 1.9.54)

- **Wrong belief (1.9.54): a two-segment Going | Interested control on every agenda
  row is how a member joins the crew's plan from the hub.** Paulo saw it live
  (revision 00071) and did not like the options it offers. Cost: a control on
  every row that he would not have shipped.
- **New belief: the hub reads as 1.9.53 again** — agenda rows list who marked each
  race, and marking happens on the event page. `git revert -m 1 301172c` on `master`;
  the 1.9.54 changelog entry and the ARCHITECTURE sentences go with it, so the docs
  describe what is deployed. W-079 is back to `open` on the board for the PM to
  reshape or drop. No migration was involved. Follow-ups that assumed the toggle
  (W-089) are noted in `docs/DEV_NOTES.md`.
- **Verified** with a minted cookie, serving `master` from this checkout
  (`/proc/<pid>/cwd`): user 12 on `/crews/<crew>` renders 200 with
  no `/crews/<crew>/attendance` form and no `aria-pressed`; a POST to
  that path is 404; the event page's own control is unchanged. Anon on the hub is
  401 as before.

## [1.9.53] — 2026-10-31

### Changed — "My crews" lives on the profile, and the nav leads to a crew (W-078, Crews v1 step 2)

- **Wrong belief (0.13.0; ARCHITECTURE § Signed-out UX and per-user visibility): one surface for the knob and the
  primitive it depends on, no separate `/crews` nav entry.** The only list of a user's crews
  sat on `/settings`, and the menu had My profile, Settings, Log out. Cost: a member who
  wanted their crew's page had to know to open Settings. Paulo's spec puts the list on the
  profile with a Crews link in the nav (decision 6, "with b").
- **New belief: your crews are part of your profile.** Own profile only (`viewer_is_self`,
  so neither preview nor a stranger sees it): My crews under the stat tiles, each row the
  crew's name linking to its hub and its member count, Create a crew in the heading, the
  Settings empty-state copy kept; its intro paragraph ("set your visibility … above")
  dropped, because nothing is above it on the profile. `CrewService.list_crews_for_user` now returns
  `(crew, member_count)` pairs — a correlated count subquery, one statement. The Settings
  section is gone and `_settings_context` no longer loads crews.
- **The nav's Crews item is `GET /crews`, a 303.** One crew → its hub; otherwise
  `/profile/{id}#crews`. A redirect rather than a per-user href in `base.html`, because
  every signed-in render would otherwise pay a crews query for a link in a closed menu.
  Anon gets the siblings' bare 401 (W-085). The hub's back link, and the create form's
  (the profile's button now opens it), read "← My profile".
- **Verified** with minted cookies, serving this worktree (`/proc/<pid>/cwd`): user 1 (no
  crews) sees the empty state and `/crews` → `/profile/1#crews`; user 12 (one) sees
  "<Crew> · 4 members" and `/crews` → `/crews/<crew>`; user 26
  (two) sees both rows with 2 and 1 members and `/crews` → `/profile/26#crews`. Member
  counts match a `GROUP BY crew_id` over `web.crew_memberships` (4, 2, 1). `/profile/14` as user 12 and
  `/profile/12?preview=1` render no My crews; `/settings` renders no Crews section; anon
  `/` is unchanged (no menu). Headless-Chrome screenshots of the curl-fetched HTML at 1280
  and 375 px for users 1 and 26. Not verified: sign-in itself, the fragment landing in a
  real browser.

## [1.9.52] — 2026-10-31

### Changed — the crew hub invites members to find their own races (W-086)

- **Wrong belief (1.9.51): the empty state's "Find a race" link was enough of a path to the
  index.** It renders only while the agenda is empty, so the moment one member marks a race
  the hub stops saying where races come from. Paulo, after the W-077 review: *"an invitation
  for members to search for their own events, without them having to figure out that they
  have to go back to index."*
- **New belief: every hub render carries the invitation.** One sentence and a plain
  `<form method="get" action="/">` with the index's `search` input, at the top of the agenda
  column above the view toggle (`crews_detail.html`). No route, no JS: `/?search=` already
  filters on name, location and terrain. The empty state keeps its message and loses the
  link, so no page prompts twice. Five lines of CSS (`.crew-find*`) reuse `.filter-input`
  and `.settings-submit`.
- **Verified** signed in with a minted cookie, serving this worktree (`/proc/<pid>/cwd`):
  member 12 on `<crew-a>` (populated, 8 rows) and member 13 on
  `<crew-b>?view=going` (empty state), each at 1280 and 375 px. The Chrome extension was
  not connected, so the screenshots are headless `google-chrome --screenshot` of the
  curl-fetched HTML with a `<base>` to the dev server, the same bytes a browser gets. The
  form sits above the fold at 375 px in both. `/?search=Kullamannen` as member 12 returns
  one tile (`tile--mine`) against 60 unfiltered. Not verified: sign-in itself, anon (401 on
  the hub, W-085).

## [1.9.51] — 2026-10-31

### Added — the crew page shows where the crew is running (W-077, Crews v1 step 1)

- **Wrong belief (PR3, `f777c87`): a crew page is a member list and an invite link.** Paulo's v1 outcome
  is *"which races the crew is converging on over the coming months"*, and nothing on
  `/crews/{slug}` named a race. Cost: a runner who joined a crew saw who was in it and nothing
  about what they were running.
- **New belief: the page is a hub — an agenda by month on the left, Members and Invite as a
  sidebar on the right, stacking under 860px.** `CrewService.list_agenda` reads members ⋈
  `web.attendance` ⋈ `core.event_occurrences` once (with the profile's `has_page` EXISTS on the
  view), then the MV once for every event id, and groups in Python. A row is one occurrence at
  least one member marked: date block (day and weekday, or TBC under its expected month), event
  name linked only when `has_page`, `event_location()` over the marked edition's MV rows (else
  the event's, the profile's fallback), that edition's distinct distances, one name chip per
  member — solid for going, dashed for interested. Chips go through `_is_identity_visible` with
  `{crew_id}` for both crew sets: every attendee here is a member of the viewer's crew, so no
  crews query. `?view=going` hides rows with no going member and the interested chips; the
  toggle is two links, no JS. **Non-past** is `not is_locked(start, end)` for a dated edition —
  W-072's rule, one day stricter than the index's `race_date >= yesterday`, chosen because W-079
  puts an attendance control on every row and a locked row would refuse it — and the index's
  month rule for TBC (first of the expected month, December if NULL, against this month). A
  multi-day edition sits under its start month (Transgrancanaria 23 Feb – 7 Mar under
  February); TBC rows sort last within their month, as on the profile.
- **Verified** on `:8000` from the worktree (`/proc/<pid>/cwd` checked), prod DB via the proxy,
  minted cookie for user 12 (member of a 4-member crew): default view lists 8
  rows in 7 months (Kullamannen 30–31 Oct still shown today, 31 Oct; Athens Half Marathon and
  Comrades under March and June 2027 as TBC); `?view=going` lists 3 rows and no dashed chip.
  User 26 (non-member) gets `crews_hidden.html`. Anon gets **401**, not a redirect — on master
  too; see DEV_NOTES. Desktop (1280) and 375px checked with headless Chrome over the saved
  render: the sidebar stacks below the agenda at 375. Empty states rendered through Jinja with
  `agenda=[]` (no live crew has zero marks). **Not exercised on live data**: an edition without
  a page — every marked non-past edition is in the view today, so `has_page` was true on all 8.

## [1.9.50] — 2026-10-31

### Changed — visibility has two levels, and one sentence each (W-076, Crews v1 step 0)

- **Wrong belief (PR2, migration 009): a runner needs a `private` level that hides them from
  everyone.** Crews v1 rule 2 says every crew a runner belongs to sees their attendance; the crew
  hub (W-077) cannot honour that for a `private` member. Paulo, IDEAS 2026-10-31: *"collapse to
  two level only."* Cost so far: none visible; the `private` rows were all
  Paulo's test accounts. The settings page and the profile banner also described the levels with different
  nouns ("name and past races" vs "profile and race calendar").
- **New belief: two levels, named for their audience, in one sentence about your calendar.**
  `_SELECTABLE_LEVELS` is `{public, crews_only}`; `visibility=private` is refused as an invalid
  level (400, same path as any unknown value). Settings and the profile banner say the same
  thing: **All indie runners** — "your calendar is visible to any signed-in indie runner" — and
  **Crews only** — "your calendar is visible to your crew" (Paulo's words, singular kept), each
  followed by the counts clause. "Public" was rejected as a label because a viewer must be
  signed in; it survives as the stored value, so no data moves for it. The profile banner's
  `else` arm is Crews only, so a still-`private` row in the deploy gap reads as the level 014
  will give it, not as open. `migrations/014_visibility_two_levels.sql` is **written, not run**:
  `UPDATE private -> crews_only`, then `users_visibility_check` (name read from `pg_constraint`)
  dropped and re-added with two values, in an explicit transaction because CI's `psql -f` is
  autocommit. The `return False` fallbacks in `_is_identity_visible` and `ProfileService._can_view`
  are untouched: they are what keeps the 3 rows hidden until 014 runs.
- **Verified** on `:8000` from the worktree (`/proc/<pid>/cwd` checked), prod DB via the proxy,
  minted cookie for user 1 (public before and after): GET /settings renders two radios and no
  `private`; POST `crews_only` → 303 `?saved=1`, re-render checked, `/profile/1` banner says
  Crews only; POST `private` → 400 with "Invalid visibility level"; POST `public` → restored,
  banner says All indie runners; `?preview=1` as a public target renders the profile under the Preview banner, as a `crews_only` target the hidden placeholder ("keeps their profile private"). Anon: `/settings` →
  303 to sign-in, `/` 200, `/profile/1` carries no banner. `privacy.html` grepped for
  `visib|crew|only you|signed`: hits are line 38 (session cookie) and 114–117 (deletion); no
  statement about who sees what, nothing to change. 1.9.49 is W-072's, still in review.
## [1.9.49] — 2026-10-30

### Fixed — attendance on a finished edition could be written but never removed (W-072)

- **Wrong belief (since `f518a38`, 2026-07-02): guarding the delete alone preserves history.**
  `clear_attendance` refused rows whose `race_date` had passed; `mark_attendance` stored any
  date. The index keeps a tile for the day after its race and a multi-day page is served to
  its last day, so a click wrote a row the UI could not undo — Remove answered 200 unchanged.
  **Cost:** W-066's developer wrote three such rows by accident and deleted them by SQL.
  **New belief:** one predicate, `is_locked(start_date, end_date)` in `AttendanceService`,
  read by mark, clear, the tile and the event page: locked the day after the occurrence's
  **last known day** (`end_date`, else `start_date`; NULL — TBC — never locks). Both routes
  answer 400 `This event has already taken place`; `attendance.js` already flashes the button
  on a non-2xx. Locked and signed in, the pages show "You are going/interested" with no
  Change/Remove, and no Going/Interested when unmarked. Anon is unchanged.
- **Paulo's ruling (2026-10-30), narrowing the spec:** the spec locked on `start_date`; Paulo
  wants a Fri–Sun festival markable through Sunday, so the lock day is `end_date`. The snapshot
  `race_date` stays `start_date` (the profile's past/upcoming split reads it). `end_date` is
  the scraper's claim: on 2026-10-30 one occurrence (6541, Athens) has a race dated after it,
  already in the scraper's IDEAS (2026-10-28); the MV is not read around it here.
- **Acceptance 0, before the fix (2026-10-30):** non-TBC occurrences in the view with
  `start_date < today`: 2 (Dublin 7837, ended 10-25; Tirana 46991, 10-25 → 11-15); with
  `coalesce(end_date, start_date) < today`: 1 (Dublin). TBC occurrences carrying an inherited
  past `race_date`: 144 — none has a `start_date`, so none locks. `web.attendance` rows with
  `race_date < created_at::date`: 0 of 57; rows locked under the old and the new rule: 30 and
  30, so no existing row changes state.
- **Verified on :8000 from the worktree** (`/proc/<pid>/cwd` checked), minted cookie for user 1
  (signed-in render, not sign-in): seeded one row on Dublin 7837 by SQL, then POST and DELETE →
  both 400, 58 rows before and after; the seed deleted by hand. Tirana 46991 (past start, future
  end): POST 200 then DELETE 200. Losheimer 100109 and TBC Berlin half 208750: mark and clear
  200. Anon POST/DELETE 401. Dublin page signed in: "You are going", no Change/Remove/Going (the
  one `attendance-btn--going` left is the calendar dialog's Save link); Tirana page: both
  buttons; anon Dublin: "Sign in to join". No locked occurrence has a tile today (Dublin's view
  rows carry no `race_date`), so the tile was rendered through Jinja in all four states.

## [1.9.48] — 2026-10-30

### Fixed — the Save-to-Google-Calendar popup stayed silent in a browser holding an old script (W-074, folds in W-064)

- **Wrong belief (ticket and PM, 2026-10-30): the popup broke between revisions `00064-l84` and
  `00065-mzr`, and "browsers revalidate `attendance.js` (`304`s on 30 Oct), so W-064's missing
  cache policy is not holding an old copy".** Those `304`s came from clients whose heuristic
  freshness had expired. Paulo's Firefox (user 12) was inside its window and sent nothing.
- **Evidence.** Production, Firefox, signed in, `/events/kullamannen/2026`: the pre-click probe
  passed, `[1, true, "function"]`, because the dialog and `data-gcal-url` are server-rendered
  HTML, which Firefox did refetch. After Change→going, no popup and no console line; then
  `[dialog.open, display, label, js.includes('offerCalendar'), js.length, transferSize,
  encodedBodySize]` = `[false, "none", "You are going", false, 9334, 0, 9336]`. 9,336 bytes is
  `attendance.js` at `57bd916`, the commit before W-023 added `offerCalendar`; production serves
  10,599 (`712bdc0`). `transferSize 0`: served from the HTTP cache, no request. Production sent
  `last-modified: Tue, 27 Oct 2026 22:06:59 GMT`, an `etag`, and **no `cache-control`**, so the
  browser chose its own freshness. After Ctrl+Shift+R the popup opened. The popup Paulo saw
  under `00064` was in Chrome; Firefox never had the new script. Same page in Chrome desktop as
  user 26 under `00065`: popup opened from the event page and from the index tile, POST `200`
  `"user_status":"going"`, no error. Nothing in the code, revision or server was wrong.
- **New belief: a static file with no cache policy and no version in its URL is fetched once
  per browser and then kept for as long as that browser likes.** Fix is W-064's, folded in on
  Paulo's word (deploy: immediate): `static_url(path)` (Jinja global, `app/main.py`) appends
  `?v=<first 8 hex of the file's md5>`, hashed once per process; every `/static/` reference in
  `base.html` and `crews_detail.html` uses it (eleven: ten and one). A file missing from the image
  is now a 500 on every page instead of a broken link; `.dockerignore` excludes none of the eleven. `StaticCacheMiddleware` sets
  `Cache-Control: public, max-age=31536000, immutable` on a `/static/` response with `?v=`, and
  `no-cache` (revalidate every time) on any other `/static/` path, which covers the
  `site.webmanifest`'s own icon paths and anything linked from outside. A deploy that changes a
  file changes its URL, which no browser has cached, so the stale copy is never consulted; the
  header only matters for the URL after that. Non-static responses are untouched.
- **How this was verified** (this worktree on :8000, `/proc/<pid>/cwd` checked). Anon `/` and
  signed-in `/events/kullamannen/2026` (minted cookie, user 1): all ten `/static/` references
  carry `?v=` (ten on `base.html`), `attendance.js?v=e138bd9f` equals `md5sum` of the file; the signed-in page still
  renders the dialog and `data-gcal-url`. `/crews/<crew>` as a member (user 12):
  `crews.js?v=9c5b4174`. Headers: versioned → `200`, `cache-control: public, max-age=31536000,
  immutable`; `attendance.js` and `favicon.ico` unversioned → `no-cache`; a `/static/` 404 →
  `no-cache`; `/` → no `cache-control`; `/static/js/nav.js?v=1` on `beta.` → `301`, no
  `cache-control` (`StaticCacheMiddleware` sits inside `CanonicalDomainMiddleware`, which stays outermost). Change demo: a byte appended to `nav.js` and the process
  restarted → `nav.js?v=c19b8aef` (its new md5) in the HTML; restored → `10b6a9bb`. Chrome on
  localhost: second page load serves all seven versioned assets with `transferSize 0`. Not
  verified: the popup on production in Firefox and Android Chrome after deploy (acceptance 1 of
  W-074 — Paulo, after this ships; no hard reload should be needed). **Confirmed in Firefox
  under `00066-4zj`, 2026-10-30 (Paulo); Android not yet.**

## [1.9.47] — 2026-10-30

### Added — GitHub in the footer's social row (W-067)

- **Paulo (2026-10-28): the footer should carry GitHub next to Strava and Instagram, linking
  to the organisation, https://github.com/indie-runners.** Third link in `.footer-social`
  (`base.html`), same attributes as its neighbours. The glyph is GitHub's own mark, unmodified:
  `GitHub_Invertocat_White.svg` from the pack https://github.com/logos links to
  (https://brand.github.com/GitHub_Logos.zip); white because the footer is `--forest`. The
  org page lists no public repository until the public flip (W-058 to W-060); Paulo chose to
  ship anyway.
- **How this was verified** (this worktree on :8000, checked via `/proc/<pid>/cwd`; signed-in
  tier is a minted cookie for user 1, which checks the render, not sign-in). `GET
  /static/icons/github.svg` → `200`, `content-type: image/svg+xml`. Headless Chrome
  screenshots of `/` and `/events/tenerife_bluetrail/2027`, anon and signed in, at 1280 and
  390 px: the footer shows the three marks in a row, Strava · Instagram · GitHub, on all
  eight. Not checked: a real click through to github.com, and a real browser's hover state.

## [1.9.46] — 2026-10-30

### Fixed — One rule for an event's location: HQ, else the first race with a start town (W-070)

- **The wrong belief: that each page could pick an event's town on its own.** The tile took
  the first-see row's `race_location` NULL or not (`race_service.py`), the hero and its
  calendar link read `event_location`, which is NULL on every row, and the profile skipped
  NULLs in SQL. **Cost:** `otf_presented_by` showed "—" on its tile and Oberaudorf on the
  profile; no hero showed a town at all. **New belief:** one function, `event_location(rows)`
  (Paulo's rule, 2026-10-28): the event's `event_location`, else the first race by
  (`race_date`, `mv_id`) with a `race_location`, else nothing. Tile, hero, both calendar links
  and the profile call it. Step 1 is empty until the scraper fills `event_location` (their
  T-039); then HQs appear everywhere with no web change. Supersedes W-055 and W-069.
- **Measured first** (read-only, one session, 2026-10-30, on the serving view; first-see as
  `row_number() OVER (PARTITION BY event_id ORDER BY race_date NULLS LAST, mv_id)`, which
  ignores the TBC `COALESCE` arm that only reorders NULL-dated rows): 396 events; **4** with a
  NULL town on the first-see row and one on a sibling (`biegi_gorskie_sanok`,
  `kielder_marathon`, `otf_presented_by`, `walt_disney_world`); **10** with no town on any race
  (8 TBC, plus `borsig_half_marathon` and `hunsbuckel_trail`); **0** with `event_location`.
  Profile: of 52 attendance rows, **0** whose attended edition has MV rows but no town while
  another edition has one — the one case where the new rule (stop at the attended edition)
  and the old SQL (fall through to any edition) would differ.
- **How this was verified** (this worktree on :8000, checked via `/proc/<pid>/cwd`; signed-in
  tier is a minted cookie for user 1, which checks the render, not sign-in). Same on both tiers
  unless said: `otf_presented_by` tile (`?date_from=2027-09-30&date_to=2027-09-30&country=germany`,
  the 60-tile cap hides it otherwise) Location `Oberaudorf`, signed-in calendar link
  `…&location=Oberaudorf`; its hero `Oberaudorf · Germany · 30 September`. Athens hero
  `Athens · Greece · 7 November`, calendar link `…&location=Athens`. `borsig_half_marathon`
  (`?search=borsig`) tile Location `—`, calendar link with no `location`, hero
  `Germany · 5 September`; `berlin_easter_run` (TBC) hero `Germany · April 2027 (TBC)` and its
  tile has no Location row, as every TBC tile. Profile: user 1 marked going on
  `otf_presented_by/2027` through the attend route, `/profile/1` showed `Otf Presented By
  Oberaudorf`, then cleared (`web.attendance` holds no row for occurrence 208583). Users 13
  and 15, signed in: every rendered town equals the old SQL's (8 of 8 and 7 of 7; Spartathlon
  empty in both). `/profile/1` with no attendance rows: 200, empty state (the MV query takes an
  empty array). Anon `/profile/13` is the sign-in wall, as before.

## [1.9.45] — 2026-10-28

### Fixed — "Who's coming" no longer reads "and 1 other" when nobody is named above it (W-066)

- **The wrong belief: that the hidden-attendee line always continues a list.** `event.html`
  rendered `and N other(s)` under each column whenever the hidden count was above zero, but
  the names above it are only the attendees the viewer may see. With every attendee in a
  column private, the list is empty and the line continues nothing. **Cost:** signed-in
  viewers read `and 1 other` under an empty "Going" on any event where only private runners
  signed up. **New belief:** the line is a sentence on its own. One `hidden_line(named, n,
  verb)` macro now serves both columns: `N indie runner(s) is/are going` with nobody named,
  `and N other indie runner(s) are going` under names. Paulo's wording, from `docs/IDEAS.md`
  2026-10-28; the `and 1 other indie runner are going` row reads as one sentence with the name
  before it (below), so it was kept rather than shown as two options. The anon block is untouched.
- **How this was verified** (this worktree on :8000, checked via `/proc/<pid>/cwd`; viewer is a
  minted cookie for user 1, which checks the signed-in render, not sign-in). No private test user
  was created: users 12 and 17 are already `private`, 13 is public. Each state was made through
  the app's own attend/clear routes on `kobolt/2026` (occurrence 46953, which nobody attended),
  then cleared; `web.attendance` holds no row for that occurrence afterwards. The column text,
  tags stripped, by case:
  - going none+1: `1 indie runner is going` · none+2: `2 indie runners are going`
  - going 1+1: `Paulo Morales Castillo and 1 other indie runner are going` · 1+2: `… and 2 other indie runners are going`
  - going 1+0: `Paulo Morales Castillo`, no line
  - interested none+1: `1 indie runner is interested` · none+2: `2 indie runners are interested`
  - interested 1+1: `… and 1 other indie runner are interested` · 1+2: `… and 2 other indie runners are interested`
  - anon, same page at none+1 and 1+2: the avatar row only, as before.
  - **A first attempt wrote three rows on past occurrences** (the app accepts attendance on a
    past date and refuses to clear it); they were deleted by hand within minutes.

## [1.9.44] — 2026-10-28

### Fixed — the event hero's meta row no longer opens with "·", and the country is capitalised (W-065)

- **The wrong belief: that the first item of the row is always there.** Each separator in
  `event.html` opened the item after it, which is right only when the location (the first item)
  is present. It is NULL on every event in the view, so every hero read `· greece · 7 November`.
  The country also printed raw where `index.html:49` and `stats.html:45` already use `| title`.
  **Cost:** a stray dot and a lower-case country on every event page, both tiers.
  **New belief:** collect the items that are present, then put a separator only between them.
  The country goes through the same `| title` as the dropdown and `/stats`. The date arm is
  unchanged in substance: TBC text, else `start – end`, else whichever date exists.
- **How this was verified** (this worktree on :8000, checked via `/proc/<pid>/cwd`; anon `curl`
  and a minted cookie for user 15, which checks the signed-in render, not sign-in; both tiers
  gave the same row on every event):
  - **Athens 2026:** `<span class="event-meta-item">Greece</span> <span class="event-meta-sep">·</span> <span class="event-meta-item">7 November</span>`.
  - **Winter Spine Race 2027 (UK, date range):** `United Kingdom · 9 January – 12 January`.
  - **hochkoenigman 2027 (country NULL):** `<span class="event-meta-item">4 June – 5 June</span>`
    alone, no separator either side. The view has three NULL-country events today:
    `hochkoenigman`, `lower_silesian_mountain`, `san_sebastian_marathon`.
  - **Athens Half 2027 (TBC):** `Greece · March 2027 (TBC)`.
  - **Not reachable live:** a location, since none exists yet (W-070). The fragment rendered
    directly with `Athens / greece / 7–8 November` gives `Athens · Greece · 7 November – 8 November`;
    with nothing at all it gives an empty `.event-meta` div, as before.
  - **Found:** the spec's example of a NULL country, `hochkoenigman`, is not `hochkoenig_ultraks`,
    which has Austria. Both are in the view.

## [1.9.43] — 2026-10-27

### Changed — hidden attendees show a runner glyph on rotating colours, not a gray "ir" (W-028)

- **The wrong belief: that one neutral placeholder reads as "someone is going".** A row of
  identical gray "ir" circles reads as empty slots. **Cost:** every signed-out visitor saw the
  community as placeholders, and so did signed-in viewers for private and crews-only attendees.
  **New belief (Paulo's IDEAS elaboration, amended 2026-10-22):** the same glyph on five
  backgrounds, coloured by the slot's position in its row mod 5, in both tiers.
- **Shape:** `anon_avatar(index, size_cls)` in `partials/avatar_strip.html` holds Paulo's SVG
  unchanged. `attendance.js` emits the same markup with the same index, because the macro does
  not reach the client-side refresh. The palette is `--anon-bg-0..4` in `main.css`, so changing
  it needs only CSS. `.avatar--stock` and `--avatar-stock-bg` are gone. Nothing emits them now.
  Real-user avatars, `+N` and sizes are untouched. Rows keep their existing label, the count text
  on tiles and the Going/Interested heading on the event page.
- **How this was verified** (this worktree on :8000, checked via `/proc/<pid>/cwd`; master on :8001):
  - **Anon `/`:** 40 `avatar--anon` circles where master had 40 `avatar--stock`, 20 of them `lg`
    in hover overlays. No `<img>`, no `avatar--initial` and no `>ir<`.
  - **The largest live tile,** Tenerife Bluetrail at "3 going", renders `avatar--anon-0`, `-1` and
    `-2`, each with only `aria-hidden` and the SVG. No id, name or photo URL.
    Quoted: `<span class="avatar avatar--anon avatar--anon-1" aria-hidden="true"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">`.
  - **Anon event page** (Tenerife): going is `-0 -1 -2`, interested is `-0`. No `profile/` and no
    `googleusercontent`. Headless Chrome shows the glyph on green, blue and brown. `var()` in the
    SVG attributes resolves.
  - **Signed-in** (minted cookie, user 15; this checks the render, not sign-in): `/` and the
    Tenerife page are byte-identical to master.
  - **Mixed row:** the macro, rendered directly with 1 public user, 7 hidden, total 9 and cap 8,
    gives `initial, anon-1 2 3 4 0 1 2, overflow`. `buildAvatarHtml` in node, on the same input,
    gives the same sequence, and the `lg` variant keeps `avatar--lg`.
  - **Checked after merge by Paulo (2026-10-27):** a private test user marked an upcoming race, and
    a different signed-in user saw the anonymous avatar in that user's slot ("it works"). His word
    doesn't cover clicking Going or Interested in a browser, so that stays unverified.
  - **Not checked:** a tile with 5+ attendees doesn't exist. The live maximum is 3, and the tile
    cap is 3.
  - **Found:** `--anon-4` renders nowhere under today's caps (tile 3, anon event row 4). It is
    kept because the rule is mod 5, and it appears if a cap is raised.

## [1.9.42] — 2026-10-27

### Added — a "Save to Google Calendar" popup at the moment you mark going (W-023)

- **Paulo, at review handover:** only "going" offers it, and as a one-time popup, because a
  link left beside a choice already made is noise. Interested triggers nothing. This replaces
  the ticket's "a link where the user marked". The first build left a standing link on both
  surfaces, which was the wrong reading.
- **The belief tested first: that Google's template link needs no OAuth scope.** It holds. It is
  a plain link opened in the runner's own Google session. `curl -sI` on one, with no cookies,
  returns `HTTP/2 200`, the URL carries no client_id, and the sign-in scope
  (`auth_service.py:20`, `openid email profile`) and flow are untouched by this diff.
- **Shape:** `gcal_url()` (`race_service.py`) builds an all-day entry. `dates=` has an exclusive
  end, so it is the last race + 1 day. Everything is passed through `urlencode`. No start date
  or TBC means no URL. The URL rides on `data-gcal-url` (tile and event page, signed-in only).
  `attendance.js` opens a native `<dialog>` (`base.html`, signed-in only) when a POST of `going`
  comes back `going`, from the Going button or from Change. The event page spans all its races.
  It does not use `occurrence_end_date`, which ends Athens on Nov 7 while its races run to Nov 8
  (DEV_NOTES). The tile spans only the races the listing returned, so filters (W-061) and the
  past-race cut (W-012) can narrow it. Athens with `date_to=2026-11-07` gives `20261107/20261108`.
- **Location** is each surface's existing field: the tile's first-see `race_location`, and the
  event page's `event_location`, which is NULL across the view today, so its links carry no
  place yet. No race-town fallback, per Paulo's direction in DEV_NOTES (W-013).
- **How this was verified:** this worktree served on :8001 (`/proc/<pid>/cwd`; :8000 was a master
  `dev.sh`), using minted cookies, which check the render, not sign-in. URLs: Nice Cannes
  Marathon (single day) gives `20261108/20261109`, Transgrancanaria gives `20270223/20270308`,
  Tenerife Bluetrail gives `20270409/20270411`, and Berliner Silvesterlauf crosses the year
  (`20261231/20270101`). Comrades (TBC) has no URL. The click path ran in jsdom against the served
  HTML with `fetch` stubbed, so no attendance rows were written, and `showModal` was stood in by
  the `open` attribute, since jsdom lacks it. On all 45 unmarked dated tiles of `/` (user 15) and
  the Athens event page, Interested opens nothing, Change to going opens the popup with the
  event's URL, and Not now closes it. 10 TBC tiles never open it. Marked pages carry no
  calendar link, and anon `/` and event pages carry no dialog or URL. **In a real browser:** Paulo signed
  in through Google on :8000, and the localhost cookie carried to this branch on :8001. There he
  marked Mallorca Serra Tramuntana going. Real `showModal` opened it, top-left at first because the global
  `margin: 0` reset undoes the modal's centring. `margin: auto` fixed it, and he saw it centred.
  **Not checked:** Google's prefilled form itself.
- **Start times stay out.** All-day is honest while races of one event start on different days.

## [1.9.41] — 2026-10-27

### Fixed — the tile's "Registration open" badge reads registration, not lifecycle (W-021)

- **The wrong belief: that `race_status` says whether registration is open.** It is
  `core.races.status` (`active | inactive | cancelled`), so `'open' in race_status` was never
  true. **Cost:** the badge has never rendered. It was also armed: any future status containing
  `open` would have badged every tile of that race. **New belief:** registration is the race-level
  `registration_open` answer, already mapped (`core.py:69`) and already shown on `event.html`.
- **Wired through, not deleted:** the column is populated (upcoming dated events: 167 with an
  open race, 105 with a closed one, 51 with a NULL), so the badge can now tell the truth and
  agree with the detail page. Deleting it would have dropped a designed signal that has data.
- **Rule:** ANY-of-races, the same convention as formats. `EventListItem.registration_open` is
  True if any race is open, False if some race is closed and none open, None if all are NULL
  (unknown, not closed). The tile shows only True, still never on a TBC tile. `race_status`
  stays on the schema; its other uses are out of scope.
- **Visible change:** signed-out visitors see the badge too, like the tile's price and
  distances. `event.html` gates registration behind sign-in (ARCHITECTURE § event page), so
  the two surfaces differ on this one field. Flagged for review, not decided here.
- **How this was verified:** served this worktree with uvicorn on :8001 (`/proc/<pid>/cwd`
  checked; :8000 was a master `dev.sh`). Checked every tile on `/` against
  `bool_or(registration_open)` per event from the view. 60 tiles: 37 badges and 0 mismatches,
  both anon and signed-in (minted cookie, the render, not sign-in). Mixed open/closed events
  are badged and all-closed and all-NULL ones are not. The same check on master gives 0 badges.
  `/?country=fr` returns 200, and there are no errors in the server log.

## [1.9.40] — 2026-10-27

### Fixed — `tickets/BACKLOG.csv` is LF and stays LF (W-015)

- **The wrong belief: that the board's line endings don't matter.** **Cost:** every edit risked
  a whole-file diff. A Python read-modify-write normalises CRLF, so the W-007 one-cell edit came
  back as 14 lines, which is the shape of a single-writer violation. The reviewer then has to
  prove the edit innocent. **New belief:** the board is LF, and `.gitattributes`
  (`tickets/BACKLOG.csv text eol=lf`) normalises whatever an editor writes when it is added.
  **Evidence:** the ticket said all-CRLF, but `git ls-files --eol` said `i/mixed`. 42 of 61
  lines were CRLF (1-32, 40-49), the rest LF. Writers since have left both endings.
- **Scoped to the path, not `*.csv`:** it is the only CSV tracked, and a glob would cover files
  this ticket never looked at.
- **How this was verified:** `12c57f1` is the conversion alone, and
  `git diff master --ignore-cr-at-eol` on it is empty. The same Python one-cell edit gives
  42+/42- on master and 1+/1- on the branch, with `git diff --check` clean. Rewriting the whole
  file as CRLF on the branch gives an empty `git diff` and git's "CRLF will be replaced by LF"
  warning. The `status` edit on this branch is itself a one-line diff. No app code changed, so
  nothing was served.

## [1.9.39] — 2026-10-27

### Changed — the official-website link moves from the hero photo to the action card (W-013)

- **The wrong belief: that this is a cut and paste.** The link was styled for a dark photo
  (`color: #fff`, white underline). Moved unchanged it would be white on the white
  `.event-action-bar` card: right in the diff, invisible in the browser. **Cost:** none.
  Nothing was broken. Paulo asked for the link to sit after the summary and before the buttons.
- **New belief:** the link is a sibling between the `short_description` paragraph and
  `.event-attendance`, outside the summary's `{% if %}`. It is `--forest-mid` with a
  `currentColor` underline and `1rem` below it. Text, target and `rel` are unchanged. The TBC
  panel's "Visit the official website" button is untouched (out of scope).
- **How this was verified:** `dev.sh` from the worktree (`/proc/<pid>/cwd` showed
  `irw-W013` on `:8000`). Anon `curl` and a minted session cookie (user 1, signed-in render,
  not sign-in) on `athens_authentic_marathon/2026` (has a summary) and
  `marcs_backyard_ultra/2027` (no summary, TBC). In both tiers the `<header>` holds 0
  `event-website-link`, and the link comes after the description (when present) and before
  `.event-attendance`. Headless Chrome screenshots at 1280 and 390 px, both tiers: dark green
  on white, readable, with a gap above "Sign in to join" or Going/Interested. In one 390 px
  shot the photo didn't load, and the hero still rendered cleanly without the link.
  A hero with no `tile_image_url` from the data was not found or tested.

## [1.9.38] — 2026-10-27

### Added — `LICENSE` (AGPL-3.0), `README.md`, and age headers on PLAN, TODO and IDEAS (W-059)

- **The wrong belief: that a private repo's defaults are fine once it is public.** With no
  license the code is all rights reserved, the opposite of Paulo's intent. With no README,
  nothing explains `W-###`, `docs/roles/` or the Claude co-author trailers, and PLAN.md
  (2026-08-28) and TODO.md read as current direction. **Cost:** none yet. The repo is still private.
- **New belief:** `LICENSE` is the verbatim GNU text. Its only copyright line is the FSF's, so
  Paulo's notice goes in the README, where the license's "How to Apply" puts it. The README
  says how the repo is built. PLAN and TODO each say what they are and when they were last
  true (dates from the PM). IDEAS says it is an inbox, not a roadmap. TODO carries W-058's
  open Support-ticket line forward so the overwrite doesn't drop it.
- **How this was verified (docs only, no app run, no DB):** `curl -s
  https://www.gnu.org/licenses/agpl-3.0.txt | diff - LICENSE` printed nothing. "How this repo
  is built" is 65 words by `wc -w`, dated to the role split (2026-08-28, PM R1). The License
  section excepts the third-party marks in `static/icons/` (PM R1). `git diff master --stat` touches only the files the ticket names.

## [1.9.37] — 2026-10-27

### Removed — `docs/FEEDBACK.md` and senders' names, from the tree now and from history at merge

- **The wrong belief: that a file is private because the repo is.** `FEEDBACK.md` held pasted
  WhatsApp messages with the senders' names, committed 2026-07-02 (`b36db79`) and once more in a
  commit whose message names a sender (`b4d7a56`). **Cost:** none yet. Going public would publish
  it, and `git rm` alone leaves it in every earlier commit.
- **Second wrong belief (PM R1, then a wider scan): that the names live only in that file.**
  `BRIEF.md` and `IDEAS.md` use six senders' first names, some beside what they asked for.
  The tracked `.idea/workspace.xml` (until `48e04f7`) logged every commit message, the pruned one included.
- **New belief:** this branch drops the file and its FILE_TREE line, and swaps the names in
  BRIEF and IDEAS for pseudonyms (Paulo, 2026-10-27). After the merge, on a fresh clone:
  `git filter-repo --path docs/FEEDBACK.md --path .idea --invert-paths --replace-text <list>`,
  then master is force-pushed on Paulo's word. The list is outside the repo
  (`~/indierunners-private/`), because it holds the names. Its regex leaves two Unsplash
  photographers who share a first name alone. Paulo's copy of the file is there too.
- **How this was verified (scratch clone, no app run, no DB, no push):** a clone of this
  checkout with the branch merged in, the command above run on it. `git log --all` on
  `docs/FEEDBACK.md` and `.idea` is empty. `git log --all -p` plus every message: 0 hits for
  every replaced name; first names shared with two Unsplash photographers hit only their credits. Count 431 → 428: three
  commits become empty and are pruned (the two that touched only the file or `.idea`, and the
  pseudonym commit, whose change the replacement has already made). filter-repo rewrites short
  SHAs it finds in messages.
- **The real run (2026-10-27, Paulo's word):** fresh clone of origin at `79b419a`, 435 → 431
  (the dry run's three, plus a commit that reworded a changelog line quoting a search term).
  The rewritten master's tree is identical to `79b419a`'s. On a new clone after the push,
  `git log --all -- docs/FEEDBACK.md` is empty, `git rev-list --all --count` is 431, and there
  are 0 hits for every replaced name. Master was force-pushed as `3f2fab7` (lease on `79b419a`),
  and the three merged branches were deleted. The main checkout was re-cloned; its ignored
  set and full tree compared equal before the old copy was deleted. PyCharm uses that same
  checkout (Paulo). Still open: GitHub Support, to purge `refs/pull/1-2/head` and cached views.

## [1.9.36] — 2026-10-27

### Added — CI applies every web migration on top of the scraper's schema

- **The wrong belief: that a migration's dependency on `core.*` is visible before it runs.**
  002 and 005 read `core.mv_denormalized_event_data`, and 006 reads `core.event_occurrences`.
  Nothing stated which `core.*` they expect. **Cost:** a scraper-side rename or drop would
  only surface when a migration failed against live, the one place where a failure costs something.
- **New belief:** the `migrations` job in `ci.yml` states it. On a `postgres:15` service (live is
  15), it loads the scraper's `database/baseline.sql` pinned at `aad6a87` (scraper 0.80.4,
  header `baseline: 079` = that ref's newest migration). It then refreshes the MV, because the
  baseline is `WITH NO DATA` and 002/005 read it, and applies `migrations/*.sql` in order with
  `ON_ERROR_STOP`. The pin moves by hand. A bump claims this app still reads `core.*` correctly.
- **One secret, read-only.** Both repos are private, so the job checks out the scraper with
  `SCRAPER_READ_TOKEN`: a fine-grained PAT scoped to the scraper alone, Contents: read, created by
  Paulo 2026-10-27 with a one-year expiry, so it **expires 2027-10-27**. **When it expires, the scraper checkout step fails
  before any SQL runs.** That red is not a schema mismatch; renew the token. No GCP, no write.
- **How this was verified (CI, no app run, no DB session):** green on the branch
  ([run](https://github.com/indie-runners/indie-runners-web/actions/runs/40482447999)), with all 12 files applied, 001 to 013, the 004 gap expected. Red with a
  throwaway `999_probe.sql` ([run](https://github.com/indie-runners/indie-runners-web/actions/runs/40482555500)):
  `psql:migrations/999_probe.sql:1: ERROR:  column "occurrence_does_not_exist" does not exist`,
  exit 3. Green again after the revert ([run](https://github.com/indie-runners/indie-runners-web/actions/runs/40482679264)). Green on `master` after the merge, on the `push` event ([run](https://github.com/indie-runners/indie-runners-web/actions/runs/40489165639)). The runs came from draft PR #2,
  because CI does not trigger on branch pushes; the PR is closed unmerged. The backfills touch zero
  rows, so this checks names and types, not data.

## [1.9.35] — 2026-10-27

### Fixed — ARCHITECTURE dates its counts file-wide, not in one section

- **The wrong belief: that a convention stated in one section of a document holds
  across it.** W-002 dated every count in the core read model section and said "counts
  in this section" are dated. The services section kept undated counts of the same
  events: "roughly 70 of 236" for `race_format`, "57 of 234" for `cutoff_time`. The
  core read model section said 356, and before W-002 it said 233. **Cost:** one file gave
  three totals for the same events, and nothing told the reader which ones were current.
- **New belief:** the dating note now covers counts of the view "anywhere in this document". `race_format` is
  90 of 356 and `cutoff_time` is 149 of 356, both measured 2026-08-28 and taken from the
  ticket. They were not re-measured, so they are two months old and dated as such. The
  static-assets count "166 of 246 events" now carries its date (2026-08-12, 1.8.1).
- **I re-read the cutoff conclusion and kept it, with the reason spelled out.** At 42%
  coverage, a cutoff filter still drops the majority of events (every event without a
  cutoff) before it compares any hours. So "cuts harder than its hour range suggests" holds
  while most events lack a cutoff, and the sentence now says so.
- **How this was verified:** docs only, no app run. I grepped `ARCHITECTURE.md` for
  `N of M` and `N events|rows|races` and found no other undated count of the corpus.
  "16 events" (1.8.0 batch) is a past incident, dated by its release. "0 of 238 rows" is
  `web.*` and out of scope; it was not re-measured.

## [1.9.34] — 2026-10-26

### Fixed — a tile's location and terrain no longer follow the query plan

- **The wrong belief: that ordering rows by date fixes which race a tile reads.** `list_races`
  sorted by `sort_key` alone, and location, terrain, `race_status` and the mixed-currency
  price come from the first row of each event. When two races share the earliest date,
  Postgres chooses the order, and its choice moves with the plan. **Cost:** the same event
  showed a different town or terrain depending on the filters, e.g. `tenerife_bluetrail` read
  La Esperanza / trail unfiltered but Playa de los Cristianos / mixed under
  `date_from=2027-01-01`.
- **New belief:** `ORDER BY sort_key, mv_id` (`race_service.py`). The default key from the
  ticket. It makes no product claim and matches the profile's final tie-break (W-027). Scope:
  for the same surviving rows the pick is fixed. A filter that drops some of an event's races
  still changes it, by design (`?search=Esperanza` keeps only that race of Tenerife Bluetrail).
- **How this was verified.** A script called `RaceService.list_races` directly, once with no
  filter and once with `date_from=2027-01-01`. It compared location, terrain, race_status,
  price and currency on the 202 non-TBC events whose earliest race is on or after that date
  (the filter keeps those whole). **Before: 20 differed** (the W-020 note counted 24 on an
  older corpus), every one a tie. **After: 0.** Adding the 149 TBC events with an expected
  date in 2027 or later (351 in all): 31 before, 0 after. **What changes on the default page:**
  46 of 381 unfiltered tiles show a different town or terrain than master, the tied race that
  `mv_id` now picks (e.g. Transvulcania Fuencaliente → El Paso). Then uvicorn ran from the worktree on `:8050`
  (`:8000` belongs to the main checkout; checked via `/proc/<pid>/cwd`), with the existing proxy.
  `/` and `/?date_from=2027-01-01` were each fetched anon and with a minted cookie (the
  signed-in render, not sign-in; `nav-avatar-btn` appears only with the cookie). All four
  render 60 tiles, and Tenerife Bluetrail reads Playa de los Cristianos / Mixed in each.

## [1.9.33] — 2026-10-26

### Changed — the footer shows the Strava and Instagram glyphs on a row of their own

- **The wrong belief: that both companies publish a glyph we can use unmodified.** Meta does:
  `static/icons/instagram.svg` is `Instagram_Glyph_White.svg` from the asset pack on
  https://www.meta.com/brand/resources/instagram/instagram-brand/, byte-identical (`cmp`).
  Strava does not. https://developers.strava.com/guidelines/ offers two zips, "Connect with
  Strava" buttons and "Powered by / Compatible with Strava" lockups, with no bare mark and
  "Never modify, alter or animate Strava logos", so cutting the chevron out is ruled out.
  press.strava.com has no asset kit. **The gap, named as Paulo chose (DEV_NOTES 2026-10-26):**
  `static/icons/strava.svg` is the Simple Icons 13.21.0 path (CC0, the one in
  `mockup_reference.html:21`) with `fill="#fff"` added. It comes from a third party, and
  Strava publishes nothing to check it against. White is a colour Strava's own lockups ship in.
- **New belief:** the text links' hrefs, `target` and `rel` are unchanged (routed check 22).
  They are now a `.footer-social` row, `flex-basis: 100%` so it wraps under the text links.
  Each link has `aria-label` "Indie Runners on Strava/Instagram" and an
  `<img alt="" aria-hidden="true">` 24×24, so the tap target is 24×24. Meta's rule against
  naming other networks "in the same spot" exempts a lineup of social icons, which this is.
- **How this was verified.** uvicorn from the worktree on `:8050` (`:8000` held by the main
  checkout; `/proc/<pid>/cwd` checked), existing proxy. Footer markup on `/`,
  `/events/tenerife_bluetrail/2027` and `/stats`, anon and minted cookie (signed-in render,
  not sign-in; `nav-avatar-btn` present only with the cookie): identical, both icons serve
  200 `image/svg+xml`. Headless Chrome screenshots (signed out) of all three pages at 1280 and 390 px
  wide (`/` at 390 as `?search=tenerife`, since 60 one-column tiles overrun the capture):
  the glyphs sit centred under the text row, pure white. Not checked: a screen reader.

## [1.9.32] — 2026-10-26

### Fixed — a crew name the slug cannot hold is refused at the form

- **The wrong belief: that any name `_slugify` turns into letters can be a crew URL.**
  Two cannot. "New" slugs to `new`, and `GET /crews/new` (the create form) is registered
  before `/crews/{slug}`, so the crew had no page and its invite URL was never shown. A
  name over 64 slug characters overflowed `slug VARCHAR(64)`; the `DataError` was not a
  `ValueError`, so it was a 500. **New belief:** `create_crew` checks the slug can be
  stored and served before writing: `_RESERVED_SLUGS` (next to `_slugify`, for the next
  fixed `/crews/<word>` route) gets "That name is taken", and a slug longer than the
  column (read from the model) gets "Crew name is too long". **Refuse, not truncate:**
  truncating makes two long names with one 64-character prefix collide and the second
  is told the name is taken.
- **How this was verified.** uvicorn from the worktree on `:8049` (`:8000` was held by the
  main checkout; `/proc/<pid>/cwd` checked), existing proxy. Minted cookie (signed-in
  render, not sign-in): POST "New" and " new!! " → 400, form re-rendered with "That name
  is taken"; 65 `a`s and "Crew " + 65 `a`s → 400, "Crew name is too long". Anon GET and
  POST `/crews/new` → 401, as master on `:8000`. Not run: a successful create, including
  the 64-character boundary, because it writes a real crew. The instance behind the local
  proxy (`indie-runners-db`; not checked that Cloud Run serves the same one) holds 0
  crews with slug `new` and 0 longer than 64 (read-only count).

## [1.9.31] — 2026-10-26

### Added — the footer links the Strava club and the Instagram account

- **The wrong belief: that a runner who likes the site can find the club from it.** No page
  linked either account. **Cost:** the site sent nobody to the two places the community
  actually gathers. **New belief:** the footer, the one element on every page, carries
  "Strava" and "Instagram" text links, each `target="_blank" rel="noopener noreferrer"`
  like the official website link. No icons (brand rules, W-046 out of scope).
- **How this was verified.** `scripts/dev.sh` from the worktree (`/proc/<pid>/cwd`
  checked). `/`, `/events/tenerife_bluetrail/2027` and `/stats`, anon and minted cookie
  (signed-in render, not sign-in; `nav-user-menu` present only in the latter): both links
  in the footer on all six. Headless Chrome screenshots: at 1280 px one row; at 390 px two
  centred rows (copyright, Imprint, Privacy / Terms, Stats, Strava, Instagram), on `/stats`
  and the event page. URLs: Instagram 200, title "indie runners (@weareindierunners)";
  Strava returns 403 to a bare curl or headless Chrome (bot wall) and 200 with browser
  headers, title "indie runners | Strava".

## [1.9.30] — 2026-10-26

### Fixed — a crew name that is taken is refused, not silently suffixed

- **The wrong belief: that a suffixed slug keeps two same-named crews apart.** It kept the
  URLs apart, but every page shows `display_name`, so a second "Crew A" at
  `/crews/<crew-a>-2` read exactly like the first. **Cost:** someone holding an
  invite link saw "Join <name>" and could not tell which crew it was; production has one
  such pair (W-041, counts only). **New belief:** the name is the identity a member sees,
  so a taken slug is refused with "That name is taken" and the form keeps what was typed.
  The `-2`…`-11` loop and `_SLUG_MAX_SUFFIX` are gone.
- **The unique index still decides.** No pre-check: the refusal is the `IntegrityError` on
  the `UNIQUE` slug, so two concurrent creates cannot both succeed.
- **Known side effect.** Existing suffixed slugs stay, so a new crew named "<name> 2" is
  refused as taken although no crew displays that name. The existing pair is not renamed
  here (a production `UPDATE`, Paulo's call).
- **How this was verified.** There is no local DB: `.env` reaches the one Cloud SQL
  instance through the proxy, so no attempt that would succeed was allowed to commit.
  Service, one session with `commit` swapped for `flush` and rolled back at the end:
  attempt 1 "W041 Probe Crew" → slug `w041-probe-crew`, counts (crews, memberships,
  invites) 4,6,6 → 5,7,7; attempt 2 "  w041 probe CREW " → "That name is taken", counts
  4,6,6 (the refusal's rollback also undid the uncommitted probe); so attempt 3, against a
  committed row: an existing crew's name uppercased → "That name is taken"; finally 4,6,6.
  Route, `scripts/dev.sh` from the worktree (`/proc/<pid>/cwd` checked), minted cookie
  (signed-in render, not sign-in): `POST /crews/new` with an existing name, uppercased and
  padded → 400, `<div class="settings-error">That name is taken</div>`, the input's
  `value` holds the typed text, crew count 4 before and after. Anon `POST` → 401 as
  before. Concurrency is by construction, not exercised.

## [1.9.29] — 2026-10-26

### Fixed — the index says when it is showing only part of what matched

- **The wrong belief: that "Showing N races" counts the matches.** It counted the tiles
  left after `index()` cuts the list to 60, so any filter matching more read "Showing 60
  races". **Cost:** a runner filtering by Germany saw 60 of 98 events with no sign of
  the rest, while `/stats` (1.9.18) linked there with the full number. **New belief:**
  the count is taken before the cut; above the cap the line reads "Showing 60 of 98
  races", at or below it nothing changes.
- **The true count, not a way to see the rest.** Seeing the rest means paging an
  engagement sort done in Python over every match; the count is one line, and it tells a
  runner to narrow the filter. The cap is unchanged.
- **How this was verified.** `scripts/dev.sh` from the worktree (`/proc/<pid>/cwd` checked),
  anon `curl` and a minted session cookie (signed-in render, not sign-in; the page carried
  its logout link). `.filter-results` text and `<div class="tile ` counts, both tiers alike:
  `/` "Showing 60 of 381 races", 60 tiles; `/?country=germany` "Showing 60 of 98 races",
  60 tiles (`/stats` lists Germany — 98 today); `/?country=france` "Showing 23 races",
  23 tiles; `/?country=spain` "Showing 24 races". Germany on master's code, same server:
  "Showing 60 races".

## [1.9.28] — 2026-10-26

### Changed — a restore re-deletes the accounts deleted after its restore point

- **The wrong belief: that privacy §8's 7 days end once backups expire.** A restore made
  inside those 7 days copies back every account deleted after its restore point, and
  nothing said to delete them again. **Cost:** none yet (the one restore in the audit log, 2026-06-17,
  before self-serve deletion and §8's 7-day promise). But the next restore would quietly break §8 for
  everyone who had just left. **New belief:** migration safety rule 6 says to compare user
  ids between production and the clone (restored into a new instance, never over
  production), and to re-delete the clone-only ids with
  `delete_account` before anything is copied out. It also says where the comparison stops
  working.
- **What the work disproved: that the app records whose account was deleted.**
  `delete_account` logs the id at INFO, but app logging is never configured, so the line is
  dropped. The request log only keeps *when*. That is why rule 6 has a limit (DEV_NOTES).
  A fix is the ticket's out of scope.
- **Acceptance 1** was met by W-033 (1.9.27): rule 4 no longer takes a manual snapshot.
- **How this was verified.** Docs-only, so there is no page to render. These `gcloud` reads
  were all made 2026-10-26. `sql backups list --instance indie-runners-db`, verbatim:
  ```
  ID             WINDOW_START_TIME              ERROR  STATUS      INSTANCE
  1792983600000  2026-10-26T03:00:00.000+00:00  -      SUCCESSFUL  indie-runners-db
  1792897200000  2026-10-25T03:00:00.000+00:00  -      SUCCESSFUL  indie-runners-db
  1792810800000  2026-10-24T03:00:00.000+00:00  -      SUCCESSFUL  indie-runners-db
  1792724400000  2026-10-23T03:00:00.000+00:00  -      SUCCESSFUL  indie-runners-db
  1792638000000  2026-10-22T03:00:00.000+00:00  -      SUCCESSFUL  indie-runners-db
  1792551600000  2026-10-21T03:00:00.000+00:00  -      SUCCESSFUL  indie-runners-db
  1792465200000  2026-10-20T03:00:00.000+00:00  -      SUCCESSFUL  indie-runners-db
  ```
  All seven are the daily automated backups; none is on-demand. `logging buckets list`: `_Default` keeps 30 days. A `logging read` over
  30 days found one `303` on `POST /settings/delete-account` (2026-10-23 20:12 UTC), and
  `main.py:640-649` returns 303 only after `delete_account`. The same read found no
  `Deleted account` and no `Loaded N dedicated event slugs` line. No DB query was run, so
  the id comparison is written from the schema (`web.users.id` is `BIGSERIAL`,
  `migrations/001_create_web_schema.sql:6`) and not exercised.

## [1.9.27] — 2026-10-26

### Changed — migration rule 4 points at point-in-time recovery, with its reason beside it

- **The wrong belief: that nobody could say why rule 4 exists.** The instance's own
  operation list (`gcloud sql operations list`, back to its creation on 2025-08-28) shows
  one automated backup a day, no on-demand backup in June and no restore. It lists
  operations on `indie-runners-db` only, so it reads as "nothing happened". Cloud Audit
  Logs show what did. On 2026-06-17 at 16:39 UTC, the 03:42 automated backup
  (`19c9cf49…`) was restored into a new instance `indie-runners-db-restore`, which was
  deleted at 17:44. The five rules were committed at 17:29, together with migration 002.
  **Cost:** a rule nobody has followed since, which would break privacy §8's 7-day promise
  the first time anyone did, because an on-demand backup never expires. **New belief:**
  rule 4 asked for a restore point fresher than the morning's backup. Point-in-time
  recovery gives one, and needs no extra copy. PITR was off then and turned on 2026-07-27
  (audit log: `pointInTimeRecoveryEnabled: false` in the 2026-06-17 and 2026-05-28
  patches, `true` in 2026-07-27 08:50). Rule 4 now says to confirm PITR is on and to note
  the start time, and not to take a manual snapshot. The reason is written beside it.
  Whether 002 finally lost rows is not in the logs.
- **Rules 1–3 and 5 are unchanged.** The same reading supports them: each answers 002's
  backfill-then-`DELETE` shape, and the June restore is the evidence behind the header.
- **How this was verified.** This is a docs-only change, with no page to render. The
  verification is the `gcloud` reads, all made 2026-10-26: `sql instances list` (one
  instance), `sql instances describe` (`pointInTimeRecoveryEnabled: true`,
  `transactionLogRetentionDays: 7`, `retainedBackups: 7`), `sql operations list`, and
  `logging read` for `cloudsql.instances.update` and `restoreBackup` and for the
  `indie-runners-db-restore` resource. No database connection was made.

## [1.9.26] — 2026-10-26

### Fixed — a one-day edition's hero no longer reads "29 May – 29 May"

- **The wrong belief: that an occurrence with both dates set spans more than one day.**
  `event.html` printed `start – end` whenever both existed. **Cost:** a redundant range
  on 153 of the 234 dated occurrences in the view (measured 2026-10-26). **New belief:**
  `main.py` drops the end date when it equals the start, so the template's existing
  start-only branch prints one date. The compare uses the raw ISO strings, all 10
  characters in every row (measured the same day), so two ends in different years never
  collapse. The format is unchanged (`%-d %B`). Index tiles already collapsed the range.
- **How this was verified.** `dev.sh` from this worktree, with `/proc/<pid>/cwd` showing
  `irw-W047` for the proxy and uvicorn. I curled each page anon and with a minted cookie
  for user 20 (signed-in render, not sign-in; the "Log out" link appeared only with it).
  `transylvania_100/2027` (29 May both ends) shows `29 May` in both tiers.
  `night_marathon_luxemburg/2027` shows `7 May – 8 May` in both tiers.
  `half_marathon_berlin/2027` (TBC) still shows `September 2027 (TBC)`. No row has only
  one end set, so that branch was not exercised. Its code is unchanged.

## [1.9.25] — 2026-10-25

### Changed — the 24 MB proxy binary leaves the index; CI builds the image

- **The wrong belief: that the repo had to carry `cloud-sql-proxy`.** Nothing reads the
  tracked copy. `.dockerignore` already kept it out of the image, and `scripts/dev.sh` and
  `scripts/db_proxy.sh` download it when it is missing. **Cost:** 24 MB in every checkout,
  and in every CI checkout once CI exists. **New belief:** it is a local download.
  `git rm --cached` removes it from the index, and `.gitignore` now lists it. The ticket
  had corrected the plan here: `.gitignore` never listed it, so without that line the next
  `git add .` would have put it back. History still holds it (out of scope).
- **CI:** `.github/workflows/ci.yml` runs `docker build .` on every PR and on every push
  to `master`. It uses no secrets, no GCP and no registry. It shows that the tracked tree
  builds. It does not show that `deploy.sh`'s image matches, because local builds also
  copy the gitignored imaging inputs. First green run:
  [40212247876](https://github.com/indie-runners/indie-runners-web/actions/runs/40212247876)
  on PR #1 (`9583f0a`).
- **Merging removes the binary from the main checkout too,** because git applies the
  deletion there. Copy the worktree's copy back before removing the worktree, or let
  `dev.sh` download it again.
- **How this was verified.** I ran `dev.sh` from this worktree, with nothing on :5432 or
  :8000 beforehand. `/proc/<pid>/cwd` showed the proxy and uvicorn in `irw-W045`. With the
  local copy (v1.38.0), the proxy bound and anon `/` rendered "Showing 60 races". Then I
  moved the copy aside and ran it again. It printed "Downloading…", and the legacy v1 URL
  served v1.38.3. That binary bound :5432 and `/` rendered the same page. With the binary
  present, `git status --short` does not list it. `grep -n 'secrets\|google\|gcloud\|auth'`
  on `ci.yml` is empty. I checked only the anon tier: nothing here renders differently
  for a signed-in user.

## [1.9.24] — 2026-10-25

### Fixed — the profile's location line and terrain badge had never rendered

- **The wrong belief: that `core.events` carries an event's location and type.** It has the
  columns, but they are empty: 0 of 492 rows have either value (measured 2026-10-25). So
  every profile row has always shown only the event name, date and status. **New
  belief:** the scraper stores both per race, on `core.mv_denormalized_event_data`.
  `_load_rows` now reads them from there with two scalar subqueries. The template
  is unchanged.
- **Step 1, one read-only session.** There are 46 attendance rows across 24 events.
  Only 17 of them find their own edition in the MV. 46/46 find their event, because the MV
  holds exactly one edition per event. Terrain is covered on 46/46 rows, location
  on 45/46 (Spartathlon has no `race_location`). **Choice: read from the MV,
  event-level.** The attended edition wins when present. Otherwise the edition the
  MV holds supplies the values, so 29 rows borrow another year's values. That
  assumes a series keeps its start town and terrain.
- **Reduction.** Terrain uses the event-page hero's rule: first non-NULL, longest race
  first. For location, ARCHITECTURE's tile rule (the earliest-dated race) beats the
  ticket's "hero rule", so profile and tile name the same town. `mv_id` breaks ties, so
  this does not add another W-029.
- **Premise correction for the PM:** the spec says `berlin_marathon` has left the MV
  (audit F6). On 2026-10-25 it was back, with one edition and 4 attendance rows.
- **Known edge:** `o_see_ultra` and `temnitzer_heide_lauf` hold an `other` terrain on some
  races. If one wins, it renders as an unstyled "Other" badge (only trail/road have
  colours). Neither did today.
- **How this was verified.** The app was served from this worktree on `:8000`
  (`/proc/<pid>/cwd` → `irw-W027`). I signed in with a minted cookie for user 13 (the signed-in
  render, not sign-in) and checked their own `/profile/13` and someone else's public
  `/profile/15`. All 15 rows show a terrain badge, and 14 show a location. **Past row:**
  Spartathlon (2026-09-30, Been there) shows "Mixed" and no location line. That is
  acceptance 2: zero empty `profile-race-sub` divs and zero empty badges. **Upcoming
  row:** Transgrancanaria (2027-02-23) shows "Artenara · Trail". Berlin Marathon on
  `/profile/15` is "Berlin · Road". Anon `/profile/15` still renders the placeholder,
  with no rows. The page took ~0.14 s warm. I did not render master side by side; the
  0/492 count is the evidence it showed nothing.

## [1.9.23] — 2026-10-25

### Fixed — `Race.occurrence_id` declared `Integer` against a `text` column; the rest of `core.py` checked

- **The wrong belief: that `app/models/core.py` describes the view.** It was written by
  hand and never compared with it. W-007 checked one column, `mv_id`, and found it wrong.
  **New belief, now checked on 2026-10-25:** of the 55 mapped columns, 54 match the
  view's type and one did not. `occurrence_id` is `text` in the view, like every
  `occurrence_*` column, but it was declared `Integer` / `Mapped[int | None]`.
- **Both directions, measured against master.** Python: rows came back as `str`
  (`'7837'`) under an `int` annotation. Every reader had already worked around this with
  `int(r.occurrence_id)` (`race_service.py:238`, `main.py:395`), which is why it never
  surfaced. SQL: `Race.occurrence_id == 7837` fails with `operator does not exist: text =
  integer`. No code filters on it today, so the error was waiting, not live. It is now
  `Text` / `Mapped[str | None]`, so the annotation states what arrives. The
  `int()` calls stay as they are.
- **Nullability was not free.** Postgres reports `is_nullable = YES` for every view
  column, so the view cannot contradict a declaration. The three non-optional ones
  (`mv_id`, `race_id`, `event_id`) hold 0 NULLs in 1929 rows today. Reported, not changed.
- **The view has 102 columns and the model maps 55.** The 47 unmapped ones (the
  `*_edition_year` columns, `event_status`, `race_distance_km` and others) are not
  defects: the ORM selects only mapped columns.
- **How this was verified.** I ran one `information_schema.columns` query in one session,
  then a probe script against master and the branch: returned type, plus `WHERE` with an
  `int` and a `str`. The app was served from this worktree on `:8014` (`/proc/<pid>/cwd` →
  `irw-W014`), with master on `:8015`. I compared `/`, `/events/tenerife_bluetrail/2027`
  (an occurrence with a going attendee), `/profile/15` and `/stats`, anonymous and with
  a minted cookie for user 15. All 8 pairs were byte-identical and all returned 200. The
  signed-in event page showed "You are going", and the index tile had `tile--mine`.

## [1.9.22] — 2026-10-25

### Added — `/sitemap.xml`, so crawlers can find every event page

- **The wrong belief: that crawlers would find the event pages by following links.** The site
  writes event pages to rank (the `short_description` outside the auth gate, the meta
  description), but the only way in was the index, which shows 60 tiles out of 390 events.
  So most event pages could only be reached by crawling filtered index URLs, and nobody
  had ever checked that a crawler does that. `/sitemap.xml` returned 404. **New belief:
  discovery is stated.** A `GET`/`HEAD` route next to `/robots.txt` serves a sitemaps.org
  0.9 `<urlset>`. It lists `/`, `/stats`, `/imprint`, `/privacy` and `/terms` (`/stats`
  added at Paulo's word, 2026-10-25; the spec predates it), plus one
  `https://indierunners.co/events/<slug>/<year>` per event from
  `list_races(RaceFilters())`, which is the index's query before the 60 cut. The list
  includes the TBC events, which the index links the same way. `robots.txt` gains its
  `Sitemap:` line. **Freshness: live per request**, with the reason in ARCHITECTURE
  § Crawl surface. No `lastmod` (nothing real to put in it).
- **Premise correction for the PM:** the spec's check "count `<loc>` against the event count
  the index renders anonymously" cannot hold, because the index stops at 60 (W-037). I
  compared against the pre-cut `list_races` instead.
- **How this was verified.** I ran it from this worktree on `:8000`, and `/proc/<pid>/cwd`
  pointed to `irw-W010`. `GET` → `200 application/xml`, `HEAD` → `200`, `POST` → `405`.
  `xmllint` isn't installed here, so I parsed the served bytes with
  `xml.etree`. The root is `{sitemaps.org/schemas/sitemap/0.9}urlset`, and each `<url>`
  holds only a `<loc>`. 395 `<loc>`, 0 duplicates, all on
  `https://indierunners.co/`. 390 event `<loc>` against `len(list_races)` = 390 (149 of
  them TBC). The **served** `robots.txt` was fed to `urllib.robotparser`: 0 listed URLs
  blocked, and `site_maps()` returns the sitemap URL. **Every one of the 395 URLs**,
  fetched anonymously with redirects off: all `200`, and no event page rendered
  "Event not found". Four event pages also checked by eye for `<h1>` and meta description.
  A minted-cookie signed-in fetch returned a byte-identical sitemap. Google itself was
  not exercised.

## [1.9.21] — 2026-10-24

### Added — `/robots.txt`, so crawlers are told to skip the signed-in surfaces

- **The wrong belief: that a missing `robots.txt` is neutral.** It is
  permissive: a 404 reads as "crawl everything". This site courts
  crawlers on purpose (PLAN ticket 2 puts `short_description` outside the
  auth gate), so `/settings`, profiles, crews and crew invite links were
  offered for indexing too. An invite token in a crawled URL ends up in a
  search index. The cost was measured on 2026-10-21: 35 `robots.txt`
  404s in 24h, and in 7 days 45+ bot hits on `/auth/google*`, each one
  starting an OAuth redirect and inflating any count of sign-in attempts.
  **New belief: the crawl policy is stated.** A `GET`/`HEAD` route in
  `main.py`, next to `/favicon.ico`, serves a constant body:
  `User-agent: *` and `Disallow:` for `/settings`, `/profile`, `/crews`
  and `/auth/`. The first three have no trailing slash, so the bare paths
  are covered too. Nothing else is disallowed. There's no `Sitemap:`
  line, because W-010 owns it. This is not access control: the routes
  answer exactly as before.
- **How this was verified.** The branch ran on `localhost:8006`, and
  `/proc/<pid>/cwd` showed `irw-W006`. Anon `GET` → `200`,
  `text/plain; charset=utf-8`, 87 bytes, with the body above. `HEAD` →
  `200`, same headers. Minted-cookie signed-in `GET` → `200 text/plain`.
  I fed the **served** file to `urllib.robotparser`. Allowed: `/`,
  `/events/grand_trail_templiers/2027`, `/stats`, `/privacy`, `/static/…`.
  Blocked: `/settings`, `/profile`, `/profile/1`, `/crews/foo`,
  `/crews/join/abc`, `/auth/google?next=…`, `/auth/callback`. Checked
  against the route list, no public route sits under a blocked prefix.
  `/me` and `/debug/health` aren't listed in the ticket and stay
  crawlable.

## [1.9.20] — 2026-10-24

### Fixed — a finished edition's URL redirects to the next one instead of answering raw JSON

- **The wrong belief: that an event URL lives as long as its event.** The
  serving view drops an edition the day after it runs, and `event_detail`
  matched `(slug, year)` exactly. So every bookmark, old tab and search
  result for a past edition got FastAPI's `{"detail":"Event not found"}`.
  The audit logged 3 Chrome hits in 24h, one with referer
  indierunners.co. **New belief: the slug outlives the year.** With no row
  for the year, the route looks up the slug's editions and redirects to
  the first one after the year asked for, or to the latest if there's
  none. With no edition at all, it renders `event_not_found.html`
  (status 404, link to `/`).
- **302, not 301.** The target moves every year, and D+2 retention
  (W-012) can bring the old year back for two days. A browser-cached 301
  would pin the wrong answer. **The trade-off:** an old URL now answers
  for an edition the person didn't ask for. They asked for 2026 and see
  2027, with that year's dates on the page. `?race=` is not carried over.
- **Route-local, not a shared HTML error handler.** Other 404s (`/crews`,
  join) and JSON callers are unchanged.
- **How this was verified.** The branch ran on `localhost:8040`, and
  `/proc/<pid>/cwd` showed `irw-W040`. Anon and minted-cookie signed-in,
  GET and HEAD:
  `grand_trail_templiers/2026` → `302 location: /events/grand_trail_templiers/2027`;
  `no_such_race_xyz/2026` → `404 text/html`, "We couldn't find this
  event", `← All events` to `/`; `grand_trail_templiers/2027` → `200
  text/html`, unchanged. All six audit slugs (`kustmarathon_zeeland`,
  `budapest_half_marathon`, `paris_versailles`, `odyssea_paris`,
  `ecotrail_paris`, `grand_trail_templiers`) `/2026` → 302 to `/2027`.
  `/2031` and `/1999` → `/2027`.

## [1.9.19] — 2026-10-24

### Changed — "Recently checked" on /stats shows the time, in UTC, labelled

- **The wrong belief: that the date was in UTC.** W-025 asserted it and
  never measured it. `checked_at` is a timestamptz, and psycopg returns it
  in the session `TimeZone`, which `app/db.py` never sets. A date hides a
  wrong zone most of the time, and showing the time would expose it on
  every row. **New belief: convert in code.** The template now renders
  `checked_at.astimezone(utc)` as `24 Oct 2026, 12:19 UTC`, with `utc`
  (`timezone.utc`) passed in from the route. `app/db.py` is unchanged, as
  the ticket says.
- **Measured: the session `TimeZone` is `UTC` today**, so production's
  rendered values don't change. What changes is that they no longer depend
  on it.
- **How this was verified.** The branch ran on `localhost:8039` (master's
  uvicorn holds :8000), and `/proc/<pid>/cwd` showed `irw-W039`. Anon and
  minted-cookie signed-in `/stats` both render 10 rows. Top row:
  `Gorce Ultra Trail — last checked 24 Oct 2026, 12:19 UTC`. A read-only
  session (`SET TRANSACTION READ ONLY`) gives the same event as
  `max(event_last_checked_at) AT TIME ZONE 'UTC'` =
  `2026-10-24 12:19:59.95`. I re-ran with `PGTZ=Europe/Berlin` and
  confirmed `SHOW TimeZone` returned `Europe/Berlin`. The branch still
  printed `12:19 UTC`, and master's template printed only the date in
  Berlin's zone. That closes W-025's open "renders in UTC".

## [1.9.18] — 2026-10-23

### Added — a coverage map on the stats page: upcoming events by country

- **The wrong belief: that the serving view is what a country click shows.**
  A `GROUP BY` over the view counts 389 events; the index serves 387. The
  view keeps TBC rows whose expected month has passed, and `list_races`
  drops them (Germany 103 vs 102, Lithuania 2 vs 1). Counted from the view,
  the map would promise events the click does not show. **New belief: count
  what the click runs.** The map counts distinct events over
  `RaceService.list_races(RaceFilters())`, which is the function behind
  `/?country=`. So every clickable country is non-empty by construction.
  The header is "Upcoming events by country", a separate denominator from
  "events tracked", as Paulo decided on 2026-10-21.

- **Rendering: a vendored SVG, drawn server-side, with no JS and no new
  dependency.** `@svg-maps/world` 2.0.0 (MapSVG, CC BY 4.0, credited under
  the map) is keyed by ISO alpha-2 and includes Kosovo, but it is 1.2 MB.
  Cropped to Europe and simplified to integer coordinates, it is
  `static/maps/europe.json`: 43 KB (9 KB gzipped), 66 countries. The page
  adds about 45 KB of inline SVG. Europe, not the world, because 3 of 387
  events sit outside it (US, South Africa, Comoros), and on a world map at
  phone width Europe would be a thumbnail. Those 3 and the microstates
  appear in the list. `event_country_alpha2` is newly mapped on `Race`.
  `core.events.country_code`, which is all NULL, is not used.

- **Click and accessibility.** A country with events is an `<a>` to
  `/?country=<event_country_code>`, shaded on a log scale. A country with
  none is a bare `<path>` with no link. The SVG is `aria-hidden` with
  `tabindex=-1` links. The ranked list under it, with names, counts and the
  same links, is the version for keyboard and screen-reader users. **3
  events have no country** and are left out of both.

- **How this was verified.** Branch on `localhost:8026`, because master's
  uvicorn holds :8000 (cwd checked: `irw-W026`). Anon and with a minted
  cookie (signed-in render): both tiers draw 39 shaded countries and list
  42. A raw `GROUP BY` using the index's date predicate, run at
  2026-10-23T21:16Z, matches all 42 counts, plus `None 3`. **Every one of
  the 42 links was curled, not just three:** 41 return exactly the listed
  number of tiles. Germany returns 60 of 102, because the index already caps
  at 60 (DEV_NOTES). Headless Chrome screenshots at 1200 px and 390 px show
  the map scaling and the list in two columns or one. `HEAD /stats` is 200.

## [1.9.17] — 2026-10-23

### Added — a public stats page, so visitors can see the backend moving

- **The ask (Paulo, IDEAS 2026-09-01):** "a live blog of what is happening".
  `/stats`, footer-linked, with three labelled parts: **events tracked**,
  **events checked in the last 30 days**, and the **last 10 checked**, name
  and date only. The map is W-026.

- **The belief this page must not fall into: that two event counts are
  one number.** The headline counts `core.events` (491, `status =
  'active'`); the rollup counts events the serving view holds (269 of 385).
  They are separate headings and never shown as a fraction. The rollup
  necessarily undercounts what the scraper checked: an event that has left
  the view is not in it. **"Tracked" is `active`.** All 491 rows are
  `active` today, so it matches "all rows"; `active` means a retired event
  stops counting.

- **The ticket's rules, applied.** The list has no age filter, so it is
  never empty, because runs are bursty. It says "last checked", never
  "verified", and shows no run counters. `event_last_checked_at` is newly
  mapped on `Race` as `DateTime(timezone=True)`, with a comment that its
  neighbour `event_last_scraped_at` is text. The 30-day cutoff is bound as
  an aware datetime. Dates render in UTC, date only. No event in the view
  has a NULL slug or year (0 of 385), so every row links; the template still
  guards it (W-019).

- **Cost.** Three aggregate queries, no per-row queries: 0.18 ms, 4.1 ms and
  2.9 ms (`EXPLAIN ANALYZE`, 2026-10-22). No caching. The view is the
  ceiling, and at 300–500 events it stays in single-digit milliseconds.

- **How this was verified.** Branch on `localhost:8010`, anon and with a
  minted cookie (signed-in render; `/settings` link present). Both tiers
  render the three labels, `491 events tracked`, `269 events checked in the
  last 30 days`, and 10 rows newest first (Arberland Ultratrail first). All
  10 links return 200. `HEAD /stats` is 200 with no body. The same counts,
  run directly at 2026-10-22T13:03:52Z: 491 and 269. `/`, an event page and
  a profile still render after the `Race` mapping change.
  Re-run after merging onto 1.9.16 (2026-10-23, `master` on :8000, cwd
  checked): both tiers again, 491 and 255, 10 links 200, anon `/settings` 303.

## [1.9.16] — 2026-10-23

### Fixed — a signed-out reader following the legal pages' Settings link gets sign-in, not JSON

- **The wrong belief: that `/settings` is only reached by signed-in users.**
  True until W-022 and W-034 linked it from privacy §8 and terms §9, which
  are public pages. Signed out, that link returned FastAPI's bare
  `{"detail":"not authenticated"}`. Both reviews missed it.

- **The new belief.** Anon `GET /settings` returns 303 to
  `/auth/google?next=/settings`, and the existing `next` validation and
  callback bring the reader back. `/settings` only: it is the one gated GET
  a public page links to. `/me` is a JSON endpoint where 401 is right, and
  `/profile` and `/crews/new` are linked only from signed-in pages. POSTs
  keep `get_required_user` and still answer 401.

- **How this was verified.** `dev.sh` from this worktree (`/proc/<pid>/cwd`
  checked), curl only. Anon: `GET`/`HEAD /settings` 303 to
  `/auth/google?next=/settings`, which 307s to Google with the session
  holding `{"post_login_redirect": "/settings"}`. `POST /settings` and
  `POST /settings/delete-account` 401. Signed-in (minted cookie, user 1):
  `/settings` 200 with the Delete account section. The Google round trip
  itself was not driven; the callback's pop is unchanged code.

## [1.9.15] — 2026-10-23

### Changed — the terms name the delete button; both legal pages carry a date

- **The wrong belief: that W-022 finished the deletion story by updating
  privacy §8.** Terms §9 Termination, the page a leaving user reads, still
  named email as the only route. It was not false (email still works), but
  it told users to write in for something a button now does. The privacy
  policy had no revision date at all, though W-022 changed what it promises.

- **The new belief.** Terms §9 names Settings → Delete account (a plain
  `/settings` link, matching privacy §8) and keeps email as the other route.
  The sentence only adds a route and leaves every obligation unchanged, so
  terms §11's advance notice does not apply. Terms "Last revised" moves to
  23 October 2026; privacy gets the same `legal-footnote` line under the
  lede and the maintainer comment on line 1. Wording was Paulo's call (approved
  in session). An anchor straight to the delete section went to `IDEAS.md`.

- **How this was verified.** `dev.sh` from this worktree (`/proc/<pid>/cwd`
  checked). Anon: `/terms` and `/privacy` 200, the new §9 text and both
  dates in the HTML, the Jinja maintainer comment not rendered. Signed-in
  (minted cookie, user 1): `/settings` renders the "Delete account" section
  and its form. Anon `/settings` is 401, as before.

## [1.9.14] — 2026-10-23

### Added — a user can delete their own account

- **The wrong belief: that deletion was a missing button.** The privacy page
  promised one, so it read as UI work. The real gap was that nothing
  defined what a deletion does to crews: `crews.created_by` and
  `crew_invites.created_by` are soft references, `NOT NULL` and with no FK
  (migrations 010 and 012 left this "for PR4"). A plain `DELETE` of the user
  would leave both pointing at a user who no longer exists.

- **The new belief.** `UserService.delete_account` does it all in one
  transaction. The user's attendance (past rows too), identities and
  memberships go by the DB's own `ON DELETE CASCADE`, read from
  `pg_constraint` rather than trusted from the model (W-007). For each crew
  the user is in: if no one else is in it, the crew is deleted. Otherwise
  its longest-standing remaining member, admins first, becomes admin and
  inherits `created_by` on the crew and its invites, so the invite link
  keeps working. The method refuses and rolls back if any soft ref would
  survive. It does a Core `delete()` rather than `db.delete(user)`, because
  the ORM relationships would try to NULL the `NOT NULL` `user_id`s. No DDL.
  `POST /settings/delete-account` requires typing "delete" and clears the
  session. Privacy §8 says the live rows go immediately and that backup
  copies expire within 7 days (the instance keeps 7 backups and 7 days of
  point-in-time logs; Paulo's wording, from the review). SameSite=lax blocks cross-site posts but not same-site ones, and
  a sibling subdomain such as a dangling `beta.` (W-018) is same-site, so
  this route also refuses a mismatched `Origin`.

- **Not as the ticket said.** Acceptance asked for the deleted profile URL
  to 404. It renders the private placeholder instead, as it does for any id
  that never existed: a 404 only for missing ids would reveal which ids are
  real (ARCHITECTURE § visibility). Left unchanged and raised with the PM.

- **How this was verified.** Run from this worktree (`/proc/<pid>/cwd`
  checked). Throwaway users 23 and 24 (`*@example.invalid`, never a
  real user), with three crews: one with T1 alone, one T1 created that T2
  joined, and one T2 created that T1 joined. Both users marked the same
  race over HTTP, and T1 also had a 2025 attendance row. Wrong word: 400.
  Foreign `Origin` and `beta.indierunners.co` `Origin`: 403. Anon: 401.
  Same-origin "Delete": 303 to `/`, cookie cleared, old cookie 401 on
  `/me`. Afterwards no `web.*` row holds 23 in any of the six user columns.
  The solo crew is gone, T2 is admin and `created_by` of the shared crew and
  its invites, T1 is absent from the event page's strip (T2's view and
  anon) and both crew pages, and T2 still shows. Every row of the real
  users, plus their crews, memberships and invites, hashed identical before
  and after. Re-sign-in was checked by calling
  `get_or_create_user_from_google`, not through Google: it gave id 25 with
  no history. Cleanup ran through `delete_account` too, covering the
  no-crews and last-member paths. **Not verified:** a real Google round
  trip after deletion.

## [1.9.13] — 2026-10-22

### Added — a favicon, from the logo pack

- **The wrong belief: that an app with no icon link has no favicon
  traffic.** Browsers request `/favicon.ico` at the root whatever `<head>`
  says, so every first visit logged a 404: **69 in the 7 days to
  2026-10-22** in production, the tab showing a blank page icon.

- **The change.** `base.html` carries the pack README's icon and manifest
  tags, pointed at `/static/brand/favicon/`, where Paulo committed the pack
  (`fc1fc5a`). The README and `site.webmanifest` both said
  `/static/favicon/`; the manifest's two icon paths are corrected in place
  rather than copying files to a second location. `/favicon.ico` is a
  GET + HEAD route (W-005) that redirects to the pack's `.ico`. Left out,
  as the ticket says: the README's `og:` / `twitter:` tags and
  `og-image.png`. Also left out: its `theme-color` meta, which is neither an
  icon nor a manifest tag and recolours mobile browser chrome, which nobody asked for.

- **How this was verified.** Branch on `localhost:8010`. The four tags are
  present on `/`, an event page, `/privacy` and `/profile/15`, anon and with
  a minted cookie (signed-in render; `/settings` link present). Every page
  but `mockup_reference.html` extends `base.html`. `GET` and `HEAD
  /favicon.ico` return 307 to the pack's `.ico`, which serves 200
  `image/vnd.microsoft.icon`; all six linked assets return 200 with their
  types, and the served manifest lists the brand paths. **Not verified by
  the developer:** the icon in a real browser tab, which needs a person
  looking at one. Production 404 count after deploy is the PM's check.

## [1.9.12] — 2026-10-22

### Changed — the canonical redirect is 301, twelve weeks after its gate expired

- **The wrong belief: that a temporary redirect with no tracked expiry would
  be revisited.** The apex rollout (1.7.x, 2026-07-27) shipped
  `CanonicalDomainMiddleware` as 302 on purpose, so a broken apex could be
  rolled back without browsers holding a cached 301. The gate was "~7 days
  with no apex regression". Nothing tracked it, and both ARCHITECTURE and the
  1.7.x entry stated "promote to 301 once stable" as a description of the
  current setup. It sat for twelve weeks. The 1.7.x entry is left as history;
  this one supersedes it.

- **What it cost.** Little to people, one hop either way. The cost is to
  crawlers, which W-006 and W-010 are about to address: a sitemap declaring
  apex canonical while `www.` and `beta.` answer "temporarily moved" says two
  things. The ticket overrides the source note's "skip if beta had no inbound
  links" clause for that reason.

- **The new belief.** `www.` and `beta.` are permanently apex: `status_code=301`
  at `app/main.py:68`. `_REDIRECTED_HOSTS` and `_CANONICAL_HOST` are
  unchanged. Rolling back now means waiting out browser caches, which is why
  W-018 (removing `beta.`) stays separate.

- **How this was verified.** Branch on `localhost:8010` with a `Host` header:
  `www.` and `beta.` return 301 to `indierunners.co`, path and query
  preserved (`/events/transgrancanaria/2027?race=x&a=1`), for GET and HEAD.
  The apex host returns 200 with 60 tiles. **Not verified here:** the
  production `curl -sI` checks and a real Google sign-in from the apex (the
  callback host is the canonical host). Both need a deploy, and this ticket is
  `batched`. Production still answers 302 as of 2026-10-22.

## [1.9.11] — 2026-10-22

### Fixed — the date filters judged a TBC event by last edition's date

- **The wrong belief: that a TBC row has no `race_date`, so `coalesce` falls
  through to the expected month.** `date_from` / `date_to` compared
  `coalesce(race_date, make_date(year, expected_month or 12, 1))`, commented
  as the fallback "for TBC rows". But per the scraper's 2026-09-05 contract a
  TBC row usually carries last edition's `race_date`, inherited, so the
  fallback never ran. Admission and `_sort_date` already used the expected
  month; only the filters did not.

- **What it cost.** Production, 2026-10-22: `date_from=2027-01-01` dropped
  Comrades (June 2027), Plaenterwaldlauf and Valentislauf; `date_to=2026-12-31`
  kept Comrades, Athens Half, Plaenterwaldlauf and Valentislauf, all expected
  in 2027. Across the corpus, `date_from=2027-01-01` admitted 53 TBC events
  where 167 qualify; `date_to=2026-12-31` admitted 161 where 1 does.

- **The new belief, and the mechanism.** The filters use `filter_key`: the
  expected date for a `tbc` row whether or not `race_date` is set, the old key
  otherwise. **`ORDER BY` deliberately keeps the old key.** Its only effect is
  row order before grouping, which decides first-see fields within an event;
  every row of a TBC occurrence has the same expected date, so ordering on it
  would make that choice arbitrary, while the inherited dates still order the
  races. `main.py:180` is the only caller of `list_races`, and it re-sorts
  events in Python with a TBC-aware key, so no caller sees SQL order as event
  order.

- **How this was verified.** Branch on `localhost:8010`, each event reached
  via `?search=`, anon and with a minted cookie (signed-in render; the page
  showed `/settings`). Both tiers: with `date_from=2027-01-01` all five appear;
  with `date_to=2026-12-31` none do. Against master's `list_races` run on the
  same DB, the **set of non-TBC events is identical** under three filters
  and none (174, 41, 49, 215). First-see fields (location, terrain, price) do
  differ on 5–24 non-TBC events per filter: every one has races tied at its
  earliest date; the tie order depends on which rows reach the sort,
  and the new filter changes that set. Pre-existing, not this fix; see DEV_NOTES. Without filters the
  output is identical to master's.

## [1.9.10] — 2026-10-22

### Fixed — the tile's price was one race's, rendered as the event's floor

- **The wrong belief: that the tile's price is the event's cheapest race, and
  the `+` marks a floor.** `RaceService.list_races` took `registration_price`
  on first-see, so the tile showed the earliest-dated race's price, and
  `race_tile.html` appended `+`. Same bug class ARCHITECTURE records under the
  read model; distances, formats and cutoffs were already collected per row.

- **What it cost.** Measured 2026-10-22 on non-TBC events (TBC tiles render no
  fee): of 90 with a known price, **32 showed a price above their cheapest
  race** (first race by `race_date`), 9 of them the dearest race as a minimum, and 11 showed `—` though
  their races are priced, because the earliest race was not. Production
  before/after: `3kings3hills` `EUR 159.0+` (races run 25–199), Dresden
  Marathon `EUR 10.0+` (has a free race), Gauja Trail `—`.

- **The new belief, and the mechanism.** The tile shows the range over every
  priced race: `price` is the floor, `price_max` is set only when races differ.
  The `+` is gone. NULL price is unknown and excluded, so it is never the
  floor; zero renders `Free` (`Free – EUR 185.0`). **One call the ticket did
  not settle:** 19 rows (10 events) carry a positive price with NULL currency. They are
  excluded like a NULL price, because a price in an unknown unit is as unknown
  as no price. That changes 6 non-TBC tiles against including them (e.g.
  Lavaredo `EUR 224.49 – 320.31`, not a floor of 39.7 in an unknown currency;
  `kat_100`, all NULL currency, renders `—` rather than a `None 77.95` range).
  Mixed currency, measured with the ticket's query: **0 events**. The
  check here is narrower than that query: it compares positive prices only,
  so a `0 DKK` beside `EUR` rows would still range (0 such events today). The
  fallback (earliest positive price alone, no `+`) is kept and was verified
  by reading the code, not in the browser.

- **How this was verified.** Branch on `localhost:8010`, each tile reached via
  `?search=`, read anon and with a minted cookie (signed-in render, not
  sign-in; the signed-in index shows `/settings`). Both tiers identical:
  range `Oh Meu Deus` `EUR 68.0 – 209.0`, `3kings3hills` `EUR 25.0 – 199.0`;
  same price `Terra Raetica` `EUR 59.0`; free floor Dresden `Free – EUR
  185.0`, Esrum `Free – DKK 370.0`; all free Grand Raid Ventoux `Free`; all
  unpriced Val Daran `—`; unpriced mixed with priced Gauja `EUR 39.0 – 159.0`,
  Deutsche Post `Free – EUR 160.0`.

## [1.9.9] — 2026-10-21

### Fixed — most links on a profile were 404s, because the profile never asked whether the page existed

- **The wrong belief: that an attendance row's event has a page.** The profile
  linked any row with an `event_slug` and an `occurrence_year`, read from
  `core.events` / `core.event_occurrences`, which keep every occurrence
  forever. The event page answers from the serving view, which drops a
  non-TBC race at midnight after it runs, and 404s on zero rows. So the link
  was a guess that went stale the day after each race, by construction.

- **What it cost.** Measured on this branch's DB, 2026-10-21: of the 24
  distinct event links the old condition would render, **14 returned 404** —
  every Been there row, plus `going` rows for events that left the view
  entirely (`berlin_marathon`, routed to the scraper with audit F6). The
  share only grows as the season ends.

- **The new belief, and the mechanism.** A profile links only what the view
  serves. `ProfileRow.has_page` is an `EXISTS` on
  `core.v_denormalized_event_data_upcoming` matching `event_detail`'s own
  predicate (`event_slug`, `occurrence_year` as text), added to the query
  `_load_rows` already runs — no extra round trip, no query per row.
  `EXPLAIN ANALYZE` for the largest profile (user 13, 10 rows): one index
  probe per row on `idx_mv_denorm_event_slug`, 0.67 ms total. "Has a page" is
  now decided twice, by `event_detail`'s query and by this `EXISTS`, and
  nothing enforces that they agree: a comment at `event_detail` points here,
  so a change to what the page serves must change both. An
  unlinked row keeps its name, flag and date.

- **How this was verified.** Branch on `localhost:8010`, cookies minted per
  `docs/DEV_NOTES.md` (authenticated render, not the OAuth flow). Every
  user's own profile signed in: 10 distinct links
  rendered, **all 10 return 200**, none 404. Someone else's profile signed in
  (13 → 15, public): same 7 rows and 5 links as 15 sees. A private target
  (13 → 12) renders the placeholder; anon `/profile/15` renders the
  placeholder, so anon has no links to check. Controls kept their links:
  `comrades_marathon/2027` (occurrence `tbc`, race_date past, served by the
  view's TBC arm) and upcoming `going` rows such as `transgrancanaria/2027`.
  User 12's Been there rows (O See Ultra, Berlin Marathon) render as plain
  text with their dates.

## [1.9.8] — 2026-09-08

### Removed — a shell redirect artefact that had been tracked in git since June

- **The wrong belief: that `=3.1.0` was something.** A file with that name in
  the repo root reads as deliberate — a pinned constraint, a lockfile fragment,
  something a tool wrote and something else reads. It survived three months and
  every clone precisely because nobody could dismiss it at a glance, and the
  cost of a file like this is not disk: it is that each new reader spends the
  same minute deciding it is not load-bearing.

- **What it actually is.** The output of an unquoted `pip install jinja2>=3.1.0`,
  where the shell read `>=3.1.0` as a redirect and pip's progress went into a
  file named `=3.1.0` instead of the terminal. The contents are a plain install
  log (`Collecting jinja2`, `Installing collected packages: MarkupSafe, jinja2`),
  1213 bytes, dated 2026-06-10.

- **A correction to the ticket's premise.** W-004 records the botched command as
  `pip install psycopg[binary]>=3.1.0`. It was not — the log inside is a jinja2
  install, and `requirements.txt` carries `>=3.1.0` on both lines (`psycopg`,
  `jinja2`), which is how the wrong one got picked. This changes nothing about
  the fix; it is noted because the next person to read the ticket would
  otherwise inherit a detail that the file itself contradicts.

- **It had already cost someone the minute, in June.** `.dockerignore:12` was
  the line `=3.1.0` — the artefact's name, as a path, in a file whose whole
  job is naming paths. `git log -S` dates it to `673af7d` ("deployment",
  2026-06-16), six days after the file appeared: somebody hit it while getting
  the image to build, **accommodated it rather than removing it**, and moved
  on. That is this entry's own argument made concrete — the file was never
  dismissible at a glance, and the first person to trip over it paid by
  writing a rule for it. Both halves are gone in this diff; an ignore rule for
  a deleted file is the other half of the same cleanup.

- **Evidence it is inert, and a correction to how that was established.**
  `git ls-files` matched it, so it was tracked and in every clone. An
  unfiltered `grep -rn '3\.1\.0'` over the tree now returns only the two
  `requirements.txt` constraint lines plus this repo's own prose about the
  ticket — nothing reads `=3.1.0` as a path. **The first version of this entry
  claimed that same result and was wrong**: the grep behind it carried
  `--include='*.md' --include='*.txt' --include='*.py' --include='*.sh'`,
  which cannot match `.dockerignore` — a file with no extension — and the
  sentence written from it said "across the tree". The search was narrower
  than the claim describing it, which is the way a grep lies. Caught in
  review, against a tree that disproved it. `docs/FILE_TREE.md` never listed
  the file, so no doc line goes with it.

- **What was not verified.** No Docker image was built, before or after.
  Removing an ignore rule for a file that no longer exists cannot change what
  is sent to the build context, but that is reasoning about pattern matching,
  not two builds compared. Nothing else was run: there is no runtime path to a
  file nothing names, so there is no browser check to make here, and this
  entry should not imply one was made.

## [1.9.7] — 2026-08-28

### Fixed — every public page returned 405 to `HEAD`, because the app's method surface was never stated

- **The wrong belief: that a `GET` route answers `HEAD`.** It is a reasonable
  thing to assume — HTTP defines `HEAD` as `GET` without a body, and several
  frameworks do synthesise it. FastAPI does not: `APIRoute` binds exactly the
  methods named in the decorator, so `@app.get("/")` matches `GET` and nothing
  else, and every other method falls through to a 405. Sixteen routes were
  declared `@app.get` and `grep "^@app\.head"` returned nothing, so the whole
  browse surface was affected, homepage included.

- **What it cost.** No human was ever locked out, which is why this sat
  unnoticed and why the ticket was `batched`. The cost falls entirely on
  clients that probe before fetching: link checkers, preview and unfurl bots,
  and uptime monitors. To all of them the site read as *down*. Production logs
  for the week show `ShapBot/0.1.0` taking a 405 on `/`, `/privacy`, `/terms`
  and `/imprint` in a single pass on 08-27, and a `Chrome/96` agent hitting
  `HEAD /` on a steady cadence that reads as an uptime check. The forward cost
  was larger than the present one: any alerting later built on `HEAD` would
  have been wrong from the day it was switched on, and would have looked like
  an outage rather than a bug.

- **Why this was invisible.** `curl` defaults to `GET`, so the audit's own site
  check passed on every page it tested. It took `curl -I` to see it.

- **The new belief, and the mechanism.** The method surface is now a stated
  property of each route rather than a per-route accident. Every route that
  serves a page is `@app.api_route(..., methods=["GET", "HEAD"])`. The
  alternative — an `@app.head` stacked beside each `@app.get` — was rejected
  for one reason: **it can drift.** Two decorators over one handler are two
  things to keep in sync, and the next route added will be written by copying a
  neighbour that has both, or one that does not. `api_route` states both
  methods in the single declaration that defines the route, so there is no
  second place to forget. The trade is that the decorator is wordier and no
  longer reads as the FastAPI idiom; that is worth a defect class that cannot
  come back one route at a time.

- **Scope, as a decision.** All sixteen `@app.get` routes were converted except
  `/debug/health`, which the ticket placed out of scope and which keeps
  `@app.get`. That includes the auth-gated routes, which is the part worth
  naming: `HEAD` there is not a new door. It runs the same handler and the same
  `get_required_user` dependency, so it answers exactly what `GET` answers to
  the same caller — `401` to an anonymous request for `/settings`, verified
  below, not a `200` that would tell a crawler a private page exists. `POST`
  routes were not touched.

- **How this was verified.** There is no test suite, so this is the whole of
  the evidence. Run against this branch on `localhost:8010` (port 8000 was held
  by a longer-running session on the shared checkout, which was left alone):

  - `HEAD` returns `200` with a zero-length body on `/`, `/imprint`,
    `/privacy`, `/terms` and a real event page
    (`/events/transgrancanaria/2027`); `GET` returns `200` with a body on all
    five.
  - Response headers were diffed field by field, `GET` against `HEAD` on `/`,
    excluding `Date`: **identical**, `Content-Length: 152406` included. `HEAD`
    reports the length it would have sent.
  - The negative cases hold: `HEAD /debug/health` is still `405`, and the
    attendance `POST` route is still `405` to `HEAD`.
  - Both tiers were checked, and by reading the page rather than the status
    code. Anonymous `GET /` renders 60 event cards, the real `<title>` and the
    sign-in CTA. Signed in — cookie minted per `docs/DEV_NOTES.md` — `GET /`
    renders 60 cards with the sign-in CTA gone and `/settings` and `/profile`
    links present, and `/settings` renders its own page. In each tier `HEAD`
    returned that tier's `GET` status: `200`/`200` signed in, `401`/`401`
    anonymous on `/settings`, `307` both ways on `/profile`.

  **What this does not cover, stated because a minted cookie invites the wrong
  reading:** the signed-in checks exercise the authenticated *render*, not the
  *sign-in*. The Google OAuth round trip is untouched by this branch and was
  not exercised by it. `/auth/google` and `/auth/google/callback` did gain
  `HEAD`, and only their method surface was verified, not their flow.

## [1.9.6] — 2026-08-28

### Fixed — `Race.mv_id` was mapped as `Text` against a `uuid` column, arming a 500 on any future commit mid-render

- **The wrong belief: that a defect which has been diagnosed and routed around
  is a closed defect.** It is not. The workaround is a record that the cause is
  still there. This one was found in 1.6.0 (2026-08-10, dated with `git log -S`
  on the changelog header) while building the terrain heal — an
  early `_heal_defaulted_terrain` committed on the request's session, which
  expired the in-flight `core.Race` rows, and the next attribute access 500'd
  the whole event page. It shipped with the commit moved to a separate
  `Session`, and a seven-line comment at the workaround site explaining the
  landmine. The comment was accurate and the fix was real, but between them
  they closed the ticket without disarming anything.

- **What it cost, specifically.** Nothing today, and that is what made it easy
  to leave: `mv_id` is filtered on nowhere, so ordinary reads never emit the
  failing predicate. The cost is shaped differently. The trigger is *someone
  editing unrelated code correctly* — any commit on the request session
  mid-render, which is an entirely reasonable thing to write — and the failure
  lands as a 500 on a page render, in a file that has nothing to do with the
  cause. The warning lived in `event_image_service.py`; the next person to
  re-arm it will be editing something else. It took a full debugging pass to
  find the first time, against a one-line fix.

- **The new belief.** The mapping is now `Uuid(as_uuid=False)`, matching the
  column, with the reasoning at the declaration rather than at the site of a
  workaround three files away. `as_uuid=False` keeps the Python-side value a
  plain `str`, which is what `Mapped[str]` and the rest of the app assume —
  widening to `UUID` objects would have been a larger change than this defect
  warrants.

- **A second, unadvertised correction.** Under the `Text` mapping SQLAlchemy
  applied no result processing, so psycopg handed back a `uuid.UUID` **object**
  while the annotation said `str` — visible in the reproduction below, which
  prints `UUID('2a7b3ca8-…')` before the fix and `'2a7b3ca8-…'` after. Nothing
  reads `mv_id`, so nothing depended on either. Worth recording because the
  declaration was wrong in both directions, not just in the SQL it generated.

- **The workaround stays.** The separate `Session` in `_heal_defaulted_terrain`
  is correct on its own merits — healing is opportunistic maintenance and
  should be transactionally independent of the render, an argument that never
  depended on this bug. Only its comment changed, so it no longer describes an
  armed landmine as current.

### Verified

There is no test suite (W-003), so the evidence is what was run. All of it
against the live view through the Cloud SQL proxy, read-only, one session.

- **The failure was reproduced before the fix and shown gone after**, by two
  scripts held outside the tree. Both were run against the unfixed `master`
  checkout and the branch, so the evidence is symmetric rather than a
  before-only anecdote.

  1. *The literal path from the ticket*: load a `Race`, `session.expire_all()`,
     touch an attribute. On `master`:

     ```
     (psycopg.errors.UndefinedFunction) operator does not exist: uuid = character varying
     LINE 3: ...ERE core.v_denormalized_event_data_upcoming.mv_id = $1::VARC...
     ```

     On the branch: `OK: expire-then-access completed, no error.`

  2. *The production trigger, which is not the same thing*: load five `Race`
     rows, `db.commit()` on the request session, then keep iterating — exactly
     what the 1.6.0 heal did. `expire_all()` proves the mechanism; this proves
     the scenario. Same error on `master`, same five events printed cleanly on
     the branch.

- **Both tiers render, and render identically to `master`.** The two builds
  were run side by side on ports 8011 (branch) and 8012 (unfixed `master`) and
  the responses **diffed byte for byte**:

  | Surface | Tier | Result |
  |---|---|---|
  | `/` | anon | 200, 152441 bytes — **identical** to `master` |
  | `/events/berlin_marathon/2026` | anon | 200, 5743 bytes — **identical** |
  | `/events/berlin_marathon/2026` | signed-in | 200, 14916 bytes — **identical** |

  A byte-identical diff is the right result here and is the actual claim: this
  change alters the SQL a load-by-PK emits, and nothing a page renders.

- **The page was checked, not the status code.** The anon event page is small
  because the race detail is behind `locked-panel` — confirmed as the gate
  rather than a missing block by minting a signed session cookie for an
  existing user and re-fetching: the locked panels disappear and the page grows
  to 14916 bytes carrying a real `race-table` with five `race-table-row`s,
  `42.2 km` and the `race-detail` block. Homepage carries real event links
  (`/events/berlin_marathon/2026`, `/events/o_see_ultra/2026`, …). Zero 500s
  and zero tracebacks in the app log across every request.

- **What was NOT exercised.** The signed-in tier was reached with a
  locally-minted session cookie, not a real Google OAuth sign-in, so the auth
  round trip itself is unexercised — it is untouched by this diff. Only one
  event page was rendered (`berlin_marathon`, a five-race event); no
  single-race or TBC event was checked. No deploy: this ticket is
  `deploy: batched`. No other column in `app/models/core.py` was audited for
  the same class of mismatch — deliberately out of scope, and a fair follow-up
  ticket.

## [1.9.5] — 2026-08-28

### Fixed — `ARCHITECTURE.md`'s core read model quoted measurements as if they were decisions

- **The wrong belief: that an architecture document can state a count as a
  fact.** The section read *"currently 967 rows across 233 events"*, and every
  other figure in it followed the same pattern — a bare number, undated,
  sitting in the same sentence as the reasoning it supports. Measured today the
  corpus is **1724 rows across 356 events**. It roughly doubled; the document
  did not move.

- **What it cost, specifically.** Not a bug — and that is the point worth
  stating plainly, because the temptation is to file this as "the numbers were
  old" and move on. Every conclusion in the section survived re-measurement, so
  nothing built on it was wrong. The cost is that a reader could not tell
  *which* sentences were durable. `event_location is dead` and
  `race_location is race-grained` are conclusions that hold as the corpus
  grows; `913 of 967 rows` is a snapshot with a shelf life. Written
  identically, they invite equal trust, and the reader who sizes a change
  against "233 events" is reasoning about a database 53% smaller than
  production. The word `currently` is what does the damage: it asserts
  freshness that nothing maintains.

- **The new belief: an undated absolute is a measurement pretending to be a
  decision.** So the fix is both halves, kept separate. Every count is
  re-measured and carries `measured 2026-08-28`; every *conclusion* is
  rewritten to stand without the count beside it. The section now says so
  explicitly, so the next reader knows which kind of sentence they are reading
  and that a dated number going stale is expected rather than a defect.

- **One number is kept deliberately stale, and labelled.** "Reimplementing that
  choice in SQL diverged on 11 events" is the result of a one-off experiment,
  not a standing property of the corpus — it cannot be re-measured without
  re-running the experiment. It now carries the date it entered the
  document (2026-08-10, recovered with `git log -S` on that phrase) and the
  corpus it was taken against, with a sentence saying the divergence is a property of
  the tie-break rather than of that corpus. Deleting it would have thrown away
  the evidence that produced the conclusion; reprinting it undated would have
  been the original defect again.

### Verified

**No browser check applies and none was run.** The diff is prose; it contains
no code, no template, and no query, so there is no rendered surface that could
differ across it. With no test suite the evidence here is the measurements
themselves, all taken 2026-08-28 in one read-only session against
`core.v_denormalized_event_data_upcoming`:

- **Totals**: 1724 rows / 356 events (was 967 / 233). 1–18 races per event,
  averaging 4.8.
- **`event_location` still dead**: populated on **0** of 1724 rows.
- **`race_location` still race-grained**: **90** events carry more than one
  distinct value (was 49). Populated on 1595 of 1724 rows, 342 of 356 events.
- **`short_description` still event-grained** — the claim that mattered most,
  because `RaceService` and `PLAN.md` ticket 2 both read it off a single row.
  **0** events carry more than one distinct value. Re-run **NULL-sensitively**,
  since a plain `count(DISTINCT)` ignores NULLs and would hide an event with
  the description on one race and absent on another: **also 0**. Where it is
  absent it is absent on every row of the event (10 rows across 3 events).
- **The rest of the event-grained column list** got the same NULL-sensitive
  test rather than being assumed to have held: `event_display_name`,
  `event_country_code`, `event_website_url`, `event_type`, `occurrence_year` —
  **0 violations each**. "Exactly one live occurrence per event" re-checked
  the same way: **0** events with more than one.
- **Race-level disagreement**: 278 events with >1 distance, 105 with >1 cutoff,
  56 with >1 terrain (was 163 / 41 / 21).
- **Coverage**: `short_description` on 353 of 356 events (was 229 of 233),
  `race_format` on 90 (was 70), `cutoff_time` on 149 (was 57).

Every grain claim in the section therefore still holds after the corpus nearly
doubled, so **nothing was routed to `indie-runners-scraper`** — the ticket's
standing instruction had a `core.*` finding gone the other way.

The unexercised path is the convention itself: nothing enforces that the next
number added to this file carries a date. That is left as a convention on
purpose — the ticket names scheduled re-measurement as out of scope.

### Note

`docs/ARCHITECTURE.md:210`, in the **services** section, restates the same
`race_format` coverage claim as *"roughly 70 of 236 events"* and is **left
stale by this release**, because that section is outside W-002's scope. So the
file currently disagrees with itself. Filed in `docs/DEV_NOTES.md` with the
measured replacement (90 of 356) so no further DB session is needed. Worth
noting for whoever picks it up: its denominator was **236** where the core read
model section said **233**, describing the same corpus at the same moment — two
undated counts of one thing had already drifted apart from each other, which is
the argument for the dated-number convention applied file-wide rather than a
second one-off re-measurement.

## [1.9.4] — 2026-08-28

### Fixed — `scripts/deploy.sh` pointed a public site at an unreproducible build

- **The wrong belief: that a deploy script's job is to deploy.** It ran
  `gcloud builds submit` then `gcloud run deploy` unconditionally, with `set -e`
  and nothing else. Both commands are correct. What was missing is everything
  that makes the deploy *reversible*, and the script's silence read as a claim
  that nothing needed to be.

- **What it cost, specifically.** The image is pushed untagged to
  `gcr.io/…/indie-runners-web` and overwritten on every deploy, so the image
  reference identifies nothing after the fact. The Cloud Run *revision* is the
  only durable handle on what was serving — and the script never read it. So
  the one moment an operator needs the previous revision name is the one moment
  it is no longer recoverable from anything the deploy printed. The developer
  brief already told operators to go and look it up by hand before deploying;
  that instruction existed because the script would not.

  Compounding it: nothing refused a dirty tree. A build from uncommitted code
  produces a revision whose source is in no commit, so even a correctly
  identified rollback target cannot be rebuilt.

- **The new belief: a deploy script owns the rollback, not just the roll
  forward.** `scripts/deploy.sh` now:
  - refuses a dirty tree, before the build, exiting non-zero;
  - prints the serving revision **before** traffic moves, and the deploying
    commit's short SHA;
  - prints a ready-to-paste
    `gcloud run services update-traffic … --to-revisions=<previous>=100`
    afterwards;
  - offers `--check`, which prints the serving revision and changes nothing;
  - **fails loudly if it cannot read the serving revision at all.** Under
    `set -e` a `gcloud` that errors — expired auth is the likeliest cause —
    would otherwise kill the script with no output whatsoever, `--check`
    included. Refusing to deploy is right (no readable rollback target means
    nothing to go back to); refusing silently is not, and this script's stated
    audience is an operator at 2am;
  - `set -euo pipefail` and `cd` to the repo root, so it does not depend on
    being invoked from one.

- **The rollback line carries a warning the naive form would not.** The service
  is configured `latestRevision: true`. Pinning traffic to an old revision means
  the *next* deploy creates a revision that receives no traffic — a rollback
  that silently disables deploying. The script prints `--to-latest` alongside,
  to undo the pin.

### Changed — Deliberately not imported from the scraper's `deploy.sh`

- **No test gate.** There is no test suite here (backlog `W-003`). A gate on a
  suite that does not exist is a comment, not a guard.
- **No version read from this changelog.** The scraper reads a version from its
  changelog because it *tags images with it* and rolls back by tag. This service
  deploys an untagged image and Cloud Run names the revision itself. Importing
  the version-read would add a second source of truth that guards nothing —
  the revision name is the identifier that matters here.

### Verified

No browser check applies to a deploy script, and `deploy: batched` means it was
not run end-to-end against the public site. What was actually run:

- `bash -n scripts/deploy.sh` — parses.
- **Dirty tree** (the working tree during development): refuses with the
  explanation, exits `1`, and does so **before** either `gcloud` call.
- **`--check`**, against the live service: printed
  `currently serving : indie-runners-web-00050-6xt`, exit `0`, no mutation. Run
  a second time from `/tmp`, which exercises the `cd`-to-root — though not the
  dirty-tree check it exists to protect, since `--check` returns before it.
- Cross-checked that revision against
  `gcloud run revisions list --service=indie-runners-web --region=europe-west1`
  — it is the top row, and `gcloud run revisions describe` resolves it.
- **Clean-tree happy path** with a stub `gcloud` earlier on `PATH`, recording
  its arguments instead of calling Google: the `gcloud run deploy` invocation is
  argument-for-argument identical to the one this script has always issued, the
  guard passes, and the rollback block prints naming the pre-deploy revision.
- `gcloud run services update-traffic --help` to confirm the printed
  `--to-revisions=NAME=100` and `--to-latest` spellings are the real ones.
- **`gcloud` failing outright**, with a stub that exits `1` on every call: both
  `--check` and the deploy path print the named diagnosis, pass gcloud's own
  stderr through, and exit `1` — rather than the silent death the first cut of
  this script had.

The first real deploy is the remaining unexercised path, and it is
`deploy: batched` — the next ticket that deploys exercises it.

## [1.9.3] — 2026-08-23

### Fixed — The connection pool was uncapped on a shared 25-connection instance

- `app/db.py`: `create_engine(settings.database_url)` took no pool arguments,
  so SQLAlchemy's defaults applied — `pool_size=5`, `max_overflow=10`, i.e.
  **15 connections per instance** and **75 at `maxScale=5`**.

  The instance is `db-f1-micro` with `max_connections=25`. Three are reserved
  for superusers and three are held permanently by the Cloud SQL agent, so
  **19** are available to applications — this service plus the scraper's batch
  pipelines, which take 6–8 each while they run.

- **The idle case was worse than the burst.** Overflow connections close when
  returned, but the five pooled ones are held persistently once warmed. After
  any traffic spike that scaled the service to five instances, it would hold
  **25 connections indefinitely** — over the entire budget with the site doing
  nothing, and the scraper unable to connect at all. Nothing released them:
  `pool_recycle` defaulted to `-1`.

- Now `pool_size=2, max_overflow=0`: **2 per instance, 10 at `maxScale=5`**, at
  peak and at idle alike. Verified by instantiating the engine against
  SQLAlchemy 2.0.50 rather than reading the documented defaults.

### Changed — Three settings that make the cap survivable

- **`pool_pre_ping=True`, `pool_recycle=1800`.** Not optional extras. Cloud SQL
  drops idle connections, and capping the pool makes each connection
  longer-lived, so without these the change would trade exhaustion errors for
  stale-connection errors. Pre-ping costs one round trip per checkout.
- **`pool_timeout` 30s → 10s.** Handlers are sync, so FastAPI runs them in a
  threadpool of roughly 40 against a pool of 2. On saturation a request should
  fail fast rather than occupy a thread for half a minute.
- **`application_name` set** via `connect_args`, carrying `K_REVISION`. It was
  unset, so this service's connections appeared as `(unnamed)` in
  `pg_stat_activity` and could not be told apart from anything else sharing the
  instance. Diagnosing the exhaustion took longer than it should have for
  exactly that reason.

### Changed — SQLAlchemy pinned to `<2.1`

`requirements.txt` used `sqlalchemy>=2.0.0` with no lockfile, and the
Dockerfile runs a plain `pip install`, so each image build installed whatever
was current. The pool cap's correctness depends on 2.0.x pooling semantics, so
the behaviour that was verified must be the behaviour that deploys. The other
eleven requirements remain unpinned — that is a separate change.

### Note

`max_overflow=0` converts exhaustion from an error into **queueing**. If the
site becomes sluggish under load, that is the signal the pool is genuinely too
small: raise it to 3 and re-measure rather than reverting. With
`application_name` now set, the live figure is one query:

```sql
SELECT application_name, state, count(*)
FROM pg_stat_activity WHERE backend_type = 'client backend'
GROUP BY 1, 2 ORDER BY 3 DESC;
```

## [1.9.2] — 2026-08-14

### Changed — One name for the control: "visibility", not "privacy"

- `app/templates/profile.html`: the summary's link read `Change your privacy
  settings` while the page it leads to titles the section `Visibility` and
  describes it in those terms throughout. Now `Change your visibility`.
- **"Visibility" is the term everything else already uses** — the settings
  heading, the `web.users.visibility` column, the `visibility` form field, and
  `SettingsService.update_visibility` — so the copy follows the model rather than
  the model following the copy. "Privacy" is also already spoken for by the
  Privacy Policy in the footer, which is a different kind of thing: a legal
  document about data handling, not a per-user control. Using one word for both
  invites a user to expect the policy and find a radio group.
- The three level names (`Public` / `Crews only` / `Private`) already matched the
  settings radios exactly and are unchanged. `Private` as a *level* is not the
  same word as `privacy` as a *category*, and keeping it is what makes the
  summary and the radio it refers to legible as the same thing.
- CSS classes renamed to match (`.profile-privacy*` → `.profile-visibility*`) so
  the stylesheet does not preserve the retired vocabulary.

### Fixed — Visibility link ran into the sentence above it

- `static/css/main.css`: the link is `display: table` with a small top margin, so
  it always starts its own line flush with the text above. Inline, it landed
  wherever the sentence happened to wrap — after the shorter rename it butted
  directly against "counts." and read as part of the prose rather than as an
  action. `table` rather than `block` so the box shrink-wraps to the text and the
  hover underline does not span the full card width.
- Measured: the link's left edge matches the paragraph's (197.1px in both cases)
  and its box is 122.8px against a 716.8px card.

## [1.9.1] — 2026-08-12

### Fixed — Profile row flags, badges and dates did not line up between rows

- `static/css/main.css`: `.profile-race-row` switched from flex to
  `display: grid` with `grid-template-columns: minmax(0, 1fr) 96px 60px 74px`.
  **Flex could not solve this at all** — each row is its own formatting context,
  so anything sized by its own content lines up with nothing above or below it.
  `.profile-race-main` held `flex: 1` and absorbed all the slack, which pushed
  the trailing items into a cluster that started at a different x on every row:
  the `Interested` pill is ~35px wider than `Going`, so the whole group shifted.
  Fixed trailing columns are what give them a shared edge.
- The flag takes `justify-self: start` in its column, so pills are left-aligned
  against a common edge while still sitting beside the date, rather than being
  right-ragged against it.
- **Each item is pinned with an explicit `grid-column`, and that is
  load-bearing.** The terrain badge is conditional in the template; with
  auto-placement, a row whose event has no terrain would pull its date into
  column 3 and reintroduce exactly the misalignment being fixed. Pinning makes an
  absent badge leave an empty cell instead. No template change was needed.
- The `≤600px` block gained a real phone layout. Its former
  `.profile-race-row { flex-wrap: wrap; }` became dead the moment the row stopped
  being flex, and four fixed columns (~260px) would have crushed the event name
  on a phone. Mobile now uses two columns — name and date on the first line, flag
  and terrain badge on the second.
- Measured in headless Chrome across six rows covering every shape (going,
  interested, been there, TBC, no-terrain, overlong name). At 1280px all six
  share one flag left edge (753px), one terrain left edge (863px) and one date
  right edge (1011px) — one distinct value each, where before every row differed.
  At a forced 390px layout the two-row form holds with a single flag left edge
  and **zero horizontal overflow**, the failure mode that bit the event page in
  1.5.2. Note that headless Chrome clamps window width to 500px, so the phone
  case must be forced rather than measured by shrinking the window — measuring at
  `--window-size=390` silently reports a 500px viewport and never applies the
  media query.
- CSS only — no template, service, route, or query change.

## [1.9.0] — 2026-08-12 — Release: profile race calendar and privacy summary

The profile page rewritten around what a runner actually goes there to check:
what is coming up, and how much room sits between the races they have committed
to and the ones they are still weighing. Presentation only — no route, query,
schema, or migration change, and no new data. Everything rendered was already on
`ProfileRow`.

### Changed — Profile is a forward-looking race calendar plus a past section

- `app/templates/profile.html`: the Going rows, the Been-there chip grid and the
  Interested mini-card grid are replaced by two lists sharing one row shape. A
  `Race calendar` section interleaves **going and interested** by date, so the
  time between what you are committed to and what you are only considering is
  legible at a glance — which is the point of merging those two. A `Been there`
  section carries past races below it, most recent first.
- Both render through one `race_row` Jinja macro. The flag is the only thing
  that distinguishes the two lists, so the markup must not be free to diverge.
- `app/services/profile_service.py`: new `TimelineRow(row, flag)`, plus
  `ProfileView.upcoming_timeline` and `.past_timeline`. The three shelves are
  **kept**, because the stat boxes count them; the timelines are derived from the
  same rows and are what the page lists. The flag is computed in the service so
  the template does no date arithmetic. TBC RSVPs (NULL `race_date`) sort last in
  the upcoming list via the existing `date.max` convention and render a `TBC`
  label rather than a blank date slot.
- **Past races are a separate section rather than the head of one merged
  timeline.** A single date-sorted list was built first and was wrong in
  practice: sorting everything ascending puts a runner's entire history above the
  races they still have ahead of them, which is the opposite of what a calendar
  is for. Splitting also retires the muting the merged version needed
  (`.profile-race-row--been_there`) — a section heading separates past from
  future better than a background tint, and tinting every row in a section reads
  as disabled rather than as history.
- The `Been there` section is omitted entirely when there is no history, so a new
  runner sees one section rather than an empty second heading.
- Dates now show month **and year** (`Aug 2026`), not just the day and month. In
  three separate sections the year was inferable from context; in a list spanning
  multiple editions it is not.

### Changed — Stat boxes reordered to Been there / Going / Interested

- Chronological order, matching the list below them. The Interested box remains
  self-only, unchanged; other viewers still see two boxes.

### Added — Privacy summary on your own profile, replacing a static tag

- `app/templates/profile.html`: a summary line above the stats naming the
  viewer's **actual** visibility level (`Public` / `Crews only` / `Private`) in
  the same words the settings radios use, saying what it means for the race
  calendar, and linking to `/settings`.
- Gated on `viewer_is_self`, which is already `False` in preview mode — so the
  preview keeps showing exactly what a stranger sees, with no separate check.
- **This replaces the three "Visible to your community" tags**, one per section,
  which were removed. They were static text: they asserted a single fixed level
  regardless of what the user had actually chosen, so a `private` profile told
  its owner it was visible to their community. They also rendered for every
  viewer rather than only the owner, which is the one person the statement is
  useful to.
- Wording tracks the real model rather than the intuitive one: `public` reads
  "every signed-in runner … signed-out visitors cannot", never "everyone",
  because anonymous visitors receive `profile_hidden.html` at every level.
- `static/css/main.css`: new `.profile-privacy`, `.profile-flag` (three
  variants — filled forest for Going as the committed state, neutral for Been
  there, outlined for Interested) and `.profile-race-date-tbc`. Removed the now
  orphaned `.vis-tag` family, `.profile-past-grid` / `.profile-past-chip` and
  `.profile-card-grid` / `.profile-mini-card` family; grep confirmed
  `profile.html` was the only consumer of each.
- No route, schema, query or migration change — `target_user.visibility` and
  `viewer_is_self` were already in the template context, and both timelines are
  built from rows `_load_rows` already returned.

### Verified

- Both lists rendered end to end: going and interested interleaved by date, TBC
  sorting last, past races most-recent-first in their own section.
- Privacy summary renders the correct wording for all three visibility levels,
  appears only for the profile owner, and stays absent in preview mode.
- Edge cases: a profile with no history omits the `Been there` section entirely;
  a profile with only past races shows the empty-calendar prompt above it; the
  empty state is worded for the viewer ("your calendar" vs "this calendar").
- Every class the template renders resolves to a rule in `main.css`, and no
  reference to the removed rule families survives anywhere in `app/` or
  `static/`.

## [1.8.1] — 2026-08-12

Ran the 1.8.0 tooling to completion. Dedicated coverage went from 29 events
to 166 of 246 — roughly two thirds of the index — over several sittings.
Content only; no code changed.

### Changed

- **137 more dedicated event photos.** Capitals and large cities first, then
  trail races keyed on the massif rather than the trailhead village. Every
  entry sourced through `scripts/unsplash_fetch.py`, so all carry
  `utm_source=indie_runners` attribution and triggered the Unsplash download
  endpoint.

### Notable

- **Stopped deliberately at ~two thirds rather than converting everything.**
  The remaining 80 events are where a dedicated photo stops paying for
  itself, in three distinct ways:
  - **12 have no `race_location` at all**, so there is nothing to search.
    They were always intended to stay on stock.
  - **13 share a location with another remaining event** — six more plain
    "Berlin", three "London", two each "Warszawa" and "Paris". Searching the
    same city again returns landmarks already used on other tiles, and two
    near-identical hero images read as a bug in a way one shared stock photo
    does not.
  - **The rest are small local races in places Unsplash has not
    photographed** — Rägelin, Zehdenick, Kopřivnice, Běchovice, Winschoten.
    A search there returns nothing usable, and skipping is the designed
    outcome.
- This is the state `docs/IMAGING.md` describes as the goal: stock is the
  fallback for events without a usable location or without a suitable photo,
  not the default for every non-dedicated event.
- The `mixed` stock bucket stays at 11 files. Thickening it was considered
  and rejected — with stock as a fallback, the set of events it serves
  shrinks as conversions land, so adding files there is work against a
  declining population.

## [1.8.0] — 2026-08-10 — Release: Unsplash photo tooling, 16 new dedicated photos

Offline tooling to source dedicated event photos from the Unsplash API, plus
the first two batches run through it. Deployed to Cloud Run as revision
`indie-runners-web-00041-x7x`. No migrations; nothing on the request path
changed except one optional config field.

### Shipped

**`scripts/unsplash_fetch.py`** — searches Unsplash for an event's location,
shows a contact sheet in the browser, and on your pick does every mechanical
step: triggers `links.download_location` (an API guideline requirement, and
the one most homegrown Unsplash tooling skips), downloads the original, writes
the credit entry in the exact shape `generate_dedicated_manifest.py` parses,
regenerates the manifest and publishes. `--no-publish` batches the fetches so
the library is not re-uploaded per photo. Attribution links carry
`utm_source=indie_runners` per the guidelines; the 13 pre-existing entries keep
the website popup's `utm_source=unsplash`, and both parse.

**`scripts/photo_candidates.py`** — read-only ranked shortlist of which events
to work on: engagement first, then how many events share the same stock file,
with terrain bucket pressure and an explicit count of events that cannot be
searched. Reads tile locations from `RaceService` rather than reimplementing
its grouping, after a SQL version disagreed with the rendered tile on 11
events.

**16 new dedicated photos**, taking the set from 13 to 29 events. Six city
races plus trail races where the massif, not the trailhead village, is the
recognisable subject.

**Stock is now the fallback rather than the default.** The intended end state
is that stock tiles serve events with no location data and events where no
suitable photo exists — not every non-dedicated event. This inverts an earlier
plan to thicken the thin `mixed` bucket: if the conversion works, stock serves
fewer events over time, so adding to it is wasted effort.

### Fixed

- **An undeclared `.env` key took down the whole app.** `Settings` uses
  pydantic's default `extra_forbidden`, so adding `UNSPLASH_ACCESS_KEY` to
  `.env` made every import of `app.config` raise — `uvicorn` included. The
  error names the field but not the cause. Declared as optional; any future
  local-only variable needs the same.

### Notable

- **Publishing without restarting credited the wrong photographer on 16
  events.** The image resolves by slug as soon as the blob lands, but the
  credit pill reads `web.event_images`, which only the startup hook rewrites.
  The result is silent — right photo, real photographer, wrong pairing. It is
  the licensing bug the terrain heal's dedicated-skip rule guards against,
  arriving by a different route. Fixed by the documented restart; now called
  out as non-optional in `docs/IMAGING.md`.
- **`event_location` is dead data** — NULL on all 967 MV rows, despite
  `ARCHITECTURE.md` previously listing it as an event-level field. The real
  column is `race_location`, which is race-grained and disagrees across races
  on 49 events. Table corrected.
- **Unsplash+ is excluded server-side** by the public search endpoint (verified
  across 120 results on four queries). The script's filter is a tripwire that
  prints rather than a load-bearing control.

## [1.7.0] — 2026-08-10 — Release: race format, event descriptions, advanced filters

Consolidated release covering the 2026-08-08 ticket batch and the follow-up
fixes it surfaced. Deployed to Cloud Run as revision
`indie-runners-web-00040-5r4`, serving `https://indierunners.co`. Point entries
1.5.0 through 1.6.1 below hold the per-change detail; this entry is the summary
and the record of what shipped together.

### Shipped

**Four tickets, executed in dependency rather than score order** (1.5.0). The
cutoff-filter ticket scored highest but its own status quo required an advanced
filter panel that did not exist, and the format-filter ticket is what builds
that panel — so display work came first, filters second, and each ticket
consumed the previous one's output. The cutoff ticket needed no new CSS as a
result.

- **Race format on the event page** — a `Format` column in the race selector
  table plus badges on the selected race. The column hides itself entirely when
  no race in the event has a format — 163 of 233 events at time of writing, so
  most event pages render no new column at all.
- **Event short description** — visible prose below the hero *and* a
  `<meta name="description">`, both outside the sign-in gate because the field
  is the page's SEO payload. 229 of 233 events populated.
- **Advanced filter panel** — collapsible `<details>`, race-format checkboxes,
  hidden unless an advanced filter is active.
- **Cutoff time filter** — hour range in that panel.

**Five defects fixed**, four of them found while building the above rather than
reported:

- Numeric filter inputs echoed `12.0` after the user typed `12` (1.5.3). Also
  affected the distance inputs, and had since they shipped.
- The event page dragged the whole layout past the viewport on phones (1.5.2) —
  `.event-body` is a grid whose items default to `min-width: auto`, so the race
  table inflated its column instead of scrolling inside its wrapper. Predated
  this batch; the new Format column made it visible.
- Events kept a `mixed` stock photo forever once their terrain arrived (1.6.0),
  now self-healing on read.
- Advanced filter groups sat on different baselines (1.6.1).
- A latent 500 in `attendance.js`'s DOM anchoring, caught during the 1.5.1
  action-bar rework before it could ship.

**Two UI changes on top of the tickets** (1.5.1): the description folded into
the action-bar card, and the going/interested counts removed from beside the
buttons — ~92% of event pages were opening with a literal "0 going", which is
negative social proof, and the numbers duplicated the Who's coming section.

### Notable

- **No migrations anywhere in this release.** Both new fields already existed in
  `core.v_denormalized_event_data_upcoming`; the terrain self-heal was designed
  specifically to avoid needing a `terrain_source` column. The additive-only
  migration guardrail was never approached.
- **`race_format` is a JSON array string**, so a race can carry several formats
  and the column cannot be filtered in SQL at all.
- **Advanced filters are event-level ANY matches over race-level data**, with one
  deliberate asymmetry: an event with no distance data passes a distance filter,
  but an event with no cutoff data is *excluded* by a cutoff filter.
- **Cutoff coverage is thin** — 57 of 234 events — so that filter cuts harder
  than its hour range suggests. Tracked as Ticket C.

### Known open

- **Ticket F**, found while fixing 1.6.0: `core.…upcoming.mv_id` is `uuid` in the
  database but mapped as `Text` in `app/models/core.py`. Harmless until something
  forces a load-by-primary-key, then it raises
  `operator does not exist: uuid = character varying`. One-line fix, not yet made.
- **Tickets A, B, C** — scraper-side data quality: implausible cutoff values
  (a 1-hour Berlin Marathon), one zero cutoff, and sparse cutoff coverage.
- All tickets are written up in `exports/reports/20260808_new_tickets_from_bugs.md`,
  which is **untracked** — `exports/` is gitignored, so the reports exist only on
  the author's machine. Unresolved; see that report for the decision.

### Documentation

`docs/ARCHITECTURE.md` gained the two data-model sections it was missing, which
is the gap this release's feature work exposed:

- **"The core read model"** — new. Nothing previously documented what this
  service actually reads from `core`, only incidental mentions inside prose about
  services and filters. It now records that the grain is **one row per race, not
  per event** (967 rows / 233 events), and carries an event-level vs race-level
  field table verified against production: 163 events hold more than one
  distance, 41 more than one cutoff, 21 more than one terrain. Reading a
  race-level field off `rows[0]` is a bug and has been one twice in this repo, so
  the table exists to make that mistake harder. Also documents the type quirks:
  `race_format` as a JSON array string, `occurrence_year` / `expected_month` as
  text, `cutoff_time` in hours with impossible values in the source, and `mv_id`
  as uuid-mapped-as-Text.
- **`web.event_images`** — added to "Tables owned by this service". It was the
  only table this service owns that was undocumented there, despite migrations
  007, 008 and 013 building it. Records the two CHECK constraints, why
  `stock_filename` is ignored for dedicated events, and that `terrain` is **not**
  a copy of the source `terrain_type` — the ambiguity `_heal_defaulted_terrain`
  depends on. Also names `source` and `attribution` as dead columns from
  migration 007: still mapped, written by nothing, populated in 0 of 238 rows.
- **"Index filtering"** — new section covering the two-tier form, why `<details>`
  over a JS toggle, the additive query-param contract, defensive coercion and
  format whitelisting, the repeatable-parameter gotcha, and `trimnum`.

`docs/FILE_TREE.md`: `main.py`, `models/core.py` and `models/web.py` comments now
name the behaviour and quirks above rather than just listing classes.

### SEO baseline

Captured 2026-08-10, two days after the descriptions shipped and therefore
reflecting a site whose event pages had no crawlable prose for the measured
window: **15 total visits, 10 with a referrer, 1 from Google**. Too small to
carry statistical weight; its value is establishing that organic search was
effectively not a traffic source beforehand, so sustained Google referrals from
here are attributable. Re-measure 2026-10-09, watching whether referrals land on
`/events/*` rather than `/`.

## [1.6.1] — 2026-08-10

### Fixed — Race format and Cutoff groups sat on different baselines in the advanced panel

- `static/css/main.css`: `.filters-advanced-body` switched from `align-items: flex-start` to `align-items: center`. The two filter groups have very different intrinsic heights — the format group is a single 15px row of checkboxes, the cutoff group is 36px of `.filter-input` boxes — so top-aligning them left their contents on different baselines. Measured in the browser: the format label and checkboxes centred at y=652.6 while the cutoff inputs centred at y=663.1, a **10.5px** offset, with the "Cutoff (hours)" label reading correspondingly high because a `.filter-group` centres its own label against its tallest child. After the change every label and control in the panel shares one centreline (delta **0.0px**).
- Verified the wrapped case too: at narrow widths the two groups drop onto separate rows and each stays internally aligned, so `center` does not introduce a regression where `flex-start` was previously doing useful work.
- CSS only — no template, filter logic, or query change.

## [1.6.0] — 2026-08-10

### Fixed — Events no longer keep a `mixed` stock photo forever after their terrain arrives

- `app/services/event_image_service.py`: new `_heal_defaulted_terrain`, called from `get_or_create_for_events` for rows that already exist. `_normalize_terrain(None)` returns `mixed` and rows were inserted once on first render and never revisited, so any event first seen before the scraper published its `terrain_type` kept a `mixed_*` photo permanently. Such a row now repairs itself the next time the event renders with a real terrain — filename re-picked from the correct bucket via the same `_pick_stock` used at insert time, and all three attribution columns rewritten to match, because a repaired filename with stale credits is a licensing problem rather than a cosmetic one.
- **The heal is deliberately narrow, and that is what avoids a migration.** Only rows stored as `mixed` are candidates — that value is the observable signature of the NULL default, since a legitimately-mixed event has a source terrain that normalizes to `mixed` too and therefore never triggers. So no `terrain_source` column is needed to tell the two cases apart. Only a source of `road`/`trail` fires a rewrite, which makes the repair one-shot: once a row moves off `mixed` it can never be touched again, so the 8 known events whose races carry conflicting terrain values cannot flap on every page view depending on which race row is read first. A stored `road`/`trail` whose source now reads `mixed` is left alone, keeping the policy `scripts/backfill_event_image_terrain.py` established (that direction was judged a scraper regression).
- **Dedicated slugs are skipped, and this is load-bearing.** The resolver serves dedicated events from their own photo and ignores `stock_filename`, so healing one would write a stock photographer's credit under a dedicated hero image — visibly wrong attribution until the next startup `refresh_dedicated_attributions`. Healing is therefore opt-in per call site: `get_or_create_for_events` gained an optional `dedicated_slugs` parameter and only heals when given it, so any caller without the slug cache cannot trigger a repair. `barcelona_half_marathon` (stored `mixed`, source `road`, dedicated) is the live case this protects and was verified unchanged.
- **The repair commits on its own short-lived Session, not the request's** — and this was found the hard way. The first implementation mutated the mapped rows and called `self.db.commit()`, which returned HTTP 500: committing the request session expires every object loaded in it, including the `core.Race` rows the route is still iterating, and reloading an expired `Race` fails with `operator does not exist: uuid = character varying` because the view's `mv_id` is `uuid` while `app/models/core.py` maps it as `Text`. That mapping mismatch is latent and harmless until something forces a load-by-primary-key. The heal now issues bulk `UPDATE`s on a separate `SessionLocal()` and mirrors the values onto the caller's in-memory rows, so the current request renders the healed image without the shared session ever being expired. Opportunistic maintenance being transactionally independent of the render is also the right shape on its own merits.
- `app/main.py`: both call sites pass `dedicated_slugs`. The `index` route's existing `dedicated_slugs` lookup moved three lines earlier to be available at call time. `event_detail` additionally stopped passing `first.terrain_type` — `first` is a single race row that may be NULL while a sibling carries a real terrain — and now passes the first non-NULL terrain across the occurrence's rows.
- `_normalize_terrain`'s `None → mixed` default is unchanged: the insert path still needs a bucket when terrain is genuinely unknown. The fix is the repair, not the default. `other → mixed` normalization is likewise untouched (normalized source equals stored value, so it never fires).
- No migration. Verified end-to-end against production data: `hella_hamburg_half` (stored `mixed`, source `road`) healed to `road_18_…` with the credit moving from Peter Robbins to Xiaonan You; `stockholm_marathon` (stored `road`, source `mixed`) rendered live and stayed `road`; `barcelona_half_marathon` unchanged; two further renders of the healed event produced no additional writes, confirming the one-shot property. 36 further events currently hold a defaulted `mixed` and will heal lazily as their pages render — no need to rerun the backfill script.
- Closes **Ticket D** in `exports/reports/20260808_new_tickets_from_bugs.md`. `docs/ARCHITECTURE.md`'s "recurrence hole still open by design" caveat is rewritten accordingly — that statement, and the matching note in the 1.4.0 entry below, are no longer true.

## [1.5.3] — 2026-08-10

### Fixed — Numeric filter inputs echoed `12.0` after the user typed `12`

- `app/main.py`: new `trimnum` Jinja filter registered on `templates.env`. Query params are coerced to `float` by `_parse_filters`, so a submitted `12` round-trips into the re-rendered input as `12.0`. The filter drops a trailing `.0` for whole numbers while preserving genuine fractions (`1.5` stays `1.5`), and returns `''` for `None` so it also replaces the `if … is not none else ''` guard the templates were carrying.
- `app/templates/index.html`: applied to all four numeric filter inputs — `cutoff_min`, `cutoff_max`, and also `distance_min` / `distance_max`, which had the same defect since the distance filter shipped. Purely a display fix; no parsing or filtering logic touched.
- Originally reported as the cutoff min/max inputs rendering at mismatched widths. Measuring them in the browser disproved that — both compute to exactly `90.0px` from the shared `.filter-input` rule, and no width mismatch ever existed. The apparent imbalance was the two extra characters of `.0` in the filled box next to an empty one, so the fix is to the value rather than the CSS.
- Verified the result set is untouched: `?cutoff_min=10&cutoff_max=16` returns 12 events and `?format=relay&cutoff_max=12` returns 22 both with and without the change, checked against `master` on the same day. (Those counts differ from the ones recorded in 1.5.0 because two days of races have since dropped out of the upcoming window — not because of this change.)

## [1.5.2] — 2026-08-08

### Fixed — Event page dragged the whole layout past the viewport on narrow screens

- `static/css/main.css`: `.event-body` and `.event-body > *` gain `min-width: 0`. `.event-body` is a CSS grid, and grid (like flex) items default to `min-width: auto`, meaning a child wider than its column *stretches the column* rather than shrinking to fit it. The race table is legitimately wider than a phone viewport — six columns of scraped data — so instead of scrolling inside `.race-table-wrap` (which has always had the correct `overflow-x: auto`), it inflated its grid column and dragged the entire document with it. Measured on `marcs_backyard_ultra/2026` at a 500px viewport: `scrollWidth` 544 vs `clientWidth` 500, a **44px overflow**, with `.race-selector` and `.race-detail` both stretched to 544px. After the fix `scrollWidth === clientWidth` and the table scrolls within its own card.
- Symptoms this explains: detail-card values sliced mid-word (`Op…` for "Open", `Temn…` for "Temnitzer"), the `12h cutoff` stat badge pushed off-screen, the Registration column header rendering as `REGISTRAT`, and the race-detail `<h2>` running past the card edge. Because the *document* was over-wide rather than one element, `nav` and `footer` were stretched too — they sit outside `.event-body` entirely, which is why the bug looked like a global layout failure rather than a table problem.
- **Predates the 1.5.0 batch.** The table has always carried six columns and has always exceeded a phone's width; the `Format` column added in 1.5.0 widened it enough to make the clipping obvious (worst on `marcs_backyard_ultra`, whose two stacked format badges push the table furthest). Reverting that column would have hidden the symptom without fixing the cause.
- Verified no desktop regression: at 1280px, `scrollWidth === clientWidth`, and the table measures 954px against a 954px wrapper — exactly filling it with no internal scrollbar, identical to before. Re-checked at a true 390px layout viewport (page rendered inside a 390px iframe, since headless Chrome clamps window width to a 500px minimum) — every card terminates at the viewport edge and all detail values are present.
- Also removed a dead override: the `≤600px` media query carried `.event-attendance { flex-direction: row; flex-wrap: wrap; align-items: center; }`, which was needed when the action bar was a vertical stack of avatar rows. Since 1.5.1 the base rule is already a wrapping row (and `row` is the flex default), so all three declarations restated the base rule verbatim.
- Filed as Ticket E in `exports/reports/20260808_new_tickets_from_bugs.md` and fixed on its own branch, deliberately kept out of the 1.5.1 UI commit.

## [1.5.1] — 2026-08-08

### Changed — Event description moved into the action-bar card

- `app/templates/event.html`: the `.event-description` paragraph moved from a bare sibling between the hero and the action bar to the **first child of `.event-action-bar`**, above the attendance row. The page previously read as four stacked bands (hero, floating text, card, card); it now reads as three, with one card carrying "what this race is" and "am I going" together. Still outside the `{% if current_user %}` gate, so anonymous crawlability and the meta description are unaffected.
- `static/css/main.css`: `.event-description` swaps its bottom margin for `padding-bottom` plus a `1px solid var(--border)` rule, separating the prose from the controls with a hairline rather than whitespace. The `max-width: 68ch` measure moved off the paragraph onto an inner `<span>` (`.event-description > span`) — with the cap on the block, the rule stopped short at the end of the text column and floated in mid-air, reading as a rendering glitch. Text still wraps at a comfortable measure while the rule spans the full card width.
- The `.event-attendance` div and all its `data-*` attributes are untouched, so every `attendance.js` selector resolves exactly as before. This was a move of a sibling element, not a change to the attendance widget.

### Removed — Going / interested counts from the event action bar

- `app/templates/event.html`: the two `.event-attendance-count` divs ("4 going", "1 interested") are gone from the action bar. **Only the action bar** — the "Who's coming" section lower on the page is untouched and still carries the full picture (real avatars and names for signed-in viewers, silhouettes plus a `+N` overflow chip for anonymous ones), and the index tile counts, tile hover counts and `AttendanceSummary` itself are all unchanged. The Who's-coming render conditions still key on `going_count` / `interested_count`, so nothing was removed server-side.
- Rationale: there are 36 RSVPs across 19 occurrences out of 234 events, so roughly **92% of event pages were opening with a literal "0 going"**. That is negative social proof on the overwhelming majority of pages, and the numeric readout duplicated what the Who's-coming section already shows in more detail. With the counts gone, the card leads with the Going / Interested buttons instead of trailing two small grey numbers.
- `static/js/attendance.js`: dead code removed rather than left pointing at absent elements. `updateEventInterested` existed **solely** to maintain the interested count in the action bar, so the whole function is deleted along with its call site and the `eventAttCount` lookup in `updateTile`; two adjacent `if (!isEventPage)` blocks collapsed into one. Verified first that click feedback does not depend on the counts — `updateTile` swaps the buttons for the "You are going" + Change / Remove block client-side regardless — so removal costs no visible response to a click. Also verified every count lookup was already null-guarded, meaning removal would have degraded to a silent no-op rather than an error; the work was deleting the now-purposeless code, not defending against a crash.
- `static/css/main.css`: orphaned `.event-attendance-count` and `.event-attendance-count--interested` rules deleted.
- `docs/ARCHITECTURE.md`: the signed-out UX section claimed anonymous visitors "always see real per-attendee counts on the index tiles and the event detail page" and called that "the fixed floor". Corrected — tiles keep their counts, and the event page still conveys attendance via the Who's-coming silhouettes and `+N` chip, but the action-bar number is gone.
- **Known open issue, filed not fixed:** the event page overflows horizontally at 390px, clipping detail values mid-word and pushing stat badges off-screen. `.event-body` is a grid whose items default to `min-width: auto`, so the race table stretches the column instead of scrolling inside `.race-table-wrap`. It predates this batch (the table always had six columns) but the new Format column made it visible. Diagnosed and verified locally, then deliberately kept out of this release as **Ticket E** in `exports/reports/20260808_new_tickets_from_bugs.md`.

## [1.5.0] — 2026-08-08

### Added — Cutoff time filter in the advanced panel

- `app/services/race_service.py`: `RaceFilters` gains `cutoff_min` / `cutoff_max` (hours, float). The grouping loop accumulates a `cutoffs` list per event on every row — same per-row rationale as formats, since cutoff is race-level and the first row seen is not necessarily the one carrying it.
- `_matches_cutoff` applies the ANY-of-races rule, but with the **opposite empty-set behaviour to `_matches_distance`**: an event with no cutoff data anywhere is *excluded* once a cutoff range is requested. Asking for races under 12h is asking for races whose cutoff is known — "unknown" is not an answer to that question, so surfacing them would be misleading. Concretely: only 57 of 234 events carry any cutoff value, so a cutoff filter is a much sharper cut than the raw hour range suggests, and that is intended. `_matches_distance` keeps its existing permissive behaviour; the asymmetry is deliberate, not an oversight.
- **Zero and negative cutoff values are dropped as bad source data** at collection time. A race cannot have a 0-hour cutoff, and admitting the value would let a junk row satisfy any `cutoff_max` query. One such row exists today (`s_25_berlin` / `kinderlauf`, `0.0`). Verified the guard works: `s_25_berlin` still matches a `cutoff_max=1` query, but via its four legitimate 0.75h races rather than the zero — the event is not wrongly excluded, only the bad value is ignored.
- Filtering stays **post-grouping even though `cutoff_time` is a real numeric column** that could go in the SQL `WHERE`. A race-level `WHERE` would drop the event's non-matching race rows before grouping, which would silently corrupt the tile's distance list and date span — the tile would advertise only the races that passed the cutoff filter. Post-grouping keeps every tile describing the whole event.
- `app/main.py`: `cutoff_min` / `cutoff_max` threaded through `_parse_filters` (reusing the existing `_float` coercion, so junk like `?cutoff_max=abc` and empty strings degrade to `None`), the `index` signature, and `has_advanced_filters` — so a cutoff-only URL opens the panel and lights up "Clear filters".
- `app/templates/index.html`: two `type="number"` inputs (`step="0.5"`, `min="0"`, `max="200"`) in the advanced panel, following the existing distance-range idiom including the en-dash separator, plus a `.filter-divider` between them and the format checkboxes. No new CSS — the panel structure from the format ticket took these as a sibling `filter-group` without modification, and `.filter-divider` is a fixed-height surface-agnostic rule that works unchanged outside the sticky bar.
- Verified end-to-end: 234 events unfiltered → 51 at `cutoff_max=12`, 16 at `cutoff_min=24`, 25 at `10–16h`, 0 at `cutoff_min=100`; `?format=relay&cutoff_max=12` composes to 13; junk and empty values leave the result set and the panel untouched; values round-trip into the inputs.
- **Source-data bug found while verifying, not fixed here** — 8 rows carry physically impossible cutoffs, including a 1-hour `bmw_berlin_marathon` (42km) and a 45-hour `s_25_berlin` half marathon. These are scraper extraction errors in `core`, which this service reads read-only, so they are written up as a ticket rather than patched in the web layer. Only the `<= 0` case is defended against here, because that one cannot be a unit-confusion misread of a real value.

### Added — Advanced filter panel with race-format filtering

- `app/templates/index.html`: new `<details class="filters-advanced">` block **inside the existing `<form>`**, below the filter bar. `<details>` was chosen over a JS toggle because it carries open/closed state, keyboard operation and focus handling natively — no new JS file, and the panel works with JavaScript disabled. It renders `open` when any advanced filter is active, so a shared or bookmarked URL carrying `?format=relay` does not look like it lost its filters. Contains one checkbox per format, `name="format"`, with `checked` driven off `filters.formats` so state round-trips through a submit.
- `app/services/race_service.py`: `RaceFilters` gains `formats: list[str]` (default-factory list, so every existing constructor keeps working). New module-level `RACE_FORMAT_CHOICES` — the single source for both the rendered checkboxes and the incoming-value whitelist — and `RACE_FORMAT_SLUGS`, its frozenset. Deliberately a **static list rather than a `DISTINCT` query** over the MV: the column holds JSON array strings, so a DISTINCT returns array literals (`'["relay", "timed"]'`) rather than slugs and would need per-request parsing to be usable. When the scraper starts emitting a new slug it must be added here — noted in a comment at the definition.
- `app/services/race_service.py` `list_races`: the grouping loop now accumulates a `formats` set per event. **Collected on every row, not just first-see** — format lives on the individual race, and the first row seen is the earliest-dated one, which frequently has no format while a later sibling does (`saintelyon/2026` is exactly this shape). Filtering happens post-grouping via `ev["formats"] & wanted_formats`: an event matches if **any** of its races carries **any** of the requested formats, the same ANY convention `_matches_distance` already uses, since tiles are event-grained while the field is race-grained. Multiple checked boxes are therefore OR, not AND — verified: relay alone 63 events, timed alone 5, both together 67, so exactly one event carries both.
- `app/main.py`: `formats: list[str] = Query(default=[], alias="format")` on `index`. **`Query` with an alias is load-bearing** — a bare `Optional[str]` parameter silently keeps only one value, so the filter would have appeared to work with one checkbox ticked and quietly dropped the rest. Explicitly tested with `?format=relay&format=timed`. `_parse_filters` takes the list and **whitelists it against `RACE_FORMAT_SLUGS`**, so `?format=zzz` cannot mark the filter set active, spring the panel open, or reach the query — verified it renders identically to an unfiltered request.
- `app/main.py`: new `has_advanced_filters` flag, keyed **only** on the advanced fields so the panel does not spring open for a plain country or date filter; it also feeds `has_active_filters` so the existing "Clear filters" link appears for a format-only filter.
- `app/templates/index.html` submit handler: the existing "disable blank fields to keep the URL clean" loop now early-returns on `type === 'checkbox'`. Checkboxes were not actually broken (a checkbox's `value` is its attribute, never `''`, and unchecked boxes are omitted by the browser anyway), but the exclusion makes the intent explicit rather than relying on that coincidence.
- `static/css/main.css`: `.filters-advanced` rule family — panel (white, bottom border, matching the `.filters-bar` surface language but **deliberately not `position: sticky`**, since an expanded panel pinned to the viewport would eat the vertical space the race grid needs), `.filters-advanced-summary` (12px forest-mid, `:focus-visible` ring in `var(--accent)`), `.filters-advanced-body` (wrapping flex row, structured so ticket 4's cutoff inputs drop in as a sibling `filter-group` with no rework), `.filter-check` (checkbox and its text as one click target, `accent-color: var(--forest-mid)`), `.filter-group--wrap`. No new colour variables.
- TBC occurrences carry `race_format` in the MV, so format filtering matches unconfirmed editions for free — 15 of the 67 relay-or-timed events are TBC. Filters also compose correctly with the existing ones (relay + Germany = 24, relay + ≥100km = 9).

### Added — Event short description, anon-visible and used as the meta description

- `app/models/core.py`: `Race` gains `short_description: Mapped[str | None]` (Text). The field is **event-level despite living on a race-grained view** — verified against production that no event carries two distinct values across its race rows — so the route reads it off `rows[0]` with no aggregation. No migration in this repo; the column already exists in the view.
- `app/services/race_service.py`: new `truncate_for_meta(text, limit=160)` helper. Source descriptions run 271–490 characters (avg 374) while search engines display roughly 155–160, so nearly every one needs trimming. Collapses whitespace, returns the text untouched when it already fits, otherwise cuts at the last space inside the limit and appends an ellipsis. Two guards: trailing punctuation is stripped before the ellipsis so nothing reads `"…,…"`, and a window with no space at all (one absurdly long token) is hard-cut rather than returned whole, so the limit holds unconditionally.
- `app/main.py` `event_detail`: `short_description` added to the `event` dict; `meta_description` computed via `truncate_for_meta` and passed separately. Both are resolved before the sign-in gate is considered — this field is deliberately part of the anonymous surface.
- `app/templates/event.html`: new `{% block head %}` emitting `<meta name="description" content="…">`, and a visible `<p class="event-description">` carrying the **full** untruncated prose, placed between the hero and the action bar. Both sit **outside** `{% if current_user %}`, so the description is in the anonymous HTML source and crawlable — that is the point of the ticket, since the visible paragraph alone is not an SEO mechanism without the meta tag. Both are individually wrapped in truthiness checks, so the 3-of-236 events with a NULL description render neither an empty tag nor an empty paragraph.
- **Removed the duplicate avatar strips from the action bar.** The going / interested `avatar_strip` calls in `.event-attendance` are gone; the counts and the Going / Interested / Change / Remove buttons stay. The strips duplicated the Who's coming section further down the same page, and their slot is where the description now goes. Worth recording that the ticket's stated reason ("they are repeated once again at the bottom of the site, for logged in users") is slightly off — the anon Who's-coming section renders silhouettes rather than real avatars, so for anonymous visitors *both* surfaces were placeholders and nothing of value is lost either way. The conclusion holds for both viewer classes; only the reasoning needed adjusting.
- `static/js/attendance.js`: **this was the non-obvious part of the removal.** `updateEventInterested` anchored its DOM insertion on `.event-attendance-avatars`, the element being deleted — so a user clicking Interested on an event with zero prior interest would have silently failed to get a rendered count. Rewritten to anchor on the going-count element instead, and the now-dead `eventAttAvatars` lookup in `updateTile` removed. `buildLgAvatarHtml` is retained — still used by the tile hover overlay.
- `static/css/main.css`: new `.event-description` (16px, `line-height: 1.65`, `max-width: 68ch` for a readable measure). `.event-attendance` switched from a vertical `flex-direction: column` stack to a wrapping horizontal row — the column layout existed to stack avatar rows above their labels, and with counts and buttons alone a row reads better. Dead `.event-attendance-avatars` and `.event-attendance-avatars--interested` rules deleted.
- Verified: anonymous requests to `london_marathon/2026` and `belgrade_marathon/2026` return the full 364 / 398-character paragraph plus a 158 / 151-character meta description cut on a word boundary; five NULL-description events emit neither tag; the signed-in path still renders counts and the description together.

### Added — Race format surfaced on the event page

- `app/models/core.py`: `Race` gains `race_format: Mapped[str | None]` (Text). The MV projects it as a **JSON array serialised to text** — `'["relay"]'`, `'["backyard_ultra", "timed"]'` — because a race can legitimately carry more than one format. Read-only mapping change; no migration in this repo (the column already exists in `core.v_denormalized_event_data_upcoming`).
- `app/services/race_service.py`: three new module-level helpers beside the existing `format_date_range` / `format_tbc_expected` display family. `parse_race_formats(raw)` json-decodes the column and returns a list of slugs, returning `[]` for every unusable shape — NULL, blank, malformed JSON (logged at WARNING), a JSON scalar instead of a list, and non-string or blank members inside an otherwise valid list — so no caller needs a guard. `format_label(slug)` maps known slugs to display labels via `_FORMAT_LABELS` (`backyard_ultra` → `Backyard Ultra`); **unknown slugs are title-cased rather than dropped**, so a new scraper value surfaces as readable text instead of silently vanishing. `race_format_labels(raw)` composes the two and dedupes while preserving order.
- `app/main.py` `event_detail`: builds a `race_formats` dict (`race_slug` → list of labels) once per request and an `any_race_formats` boolean. Keying on `race_slug` is safe — verified zero duplicate `(event_slug, occurrence_year, race_slug)` groups in the view. Parsing happens in the route, not the template, so Jinja stays free of JSON handling.
- `app/templates/event.html`: two surfaces, both inside the existing signed-in gate (consistent with every other scraped race field). (1) A `Format` column in the race selector table — the table is the at-a-glance comparison surface across an event's races, and format is exactly the kind of thing you compare across them. The `<th>` and every `<td>` are wrapped in `{% if any_race_formats %}`, so events with no format data anywhere render the table exactly as before rather than growing an empty column — which matters, because only **70 of 236 events** carry any format at all. (2) Format badges appended to `.race-detail-stats` for the selected race, beside distance / ascent / cutoff.
- `static/css/main.css`: `.race-stat--format` (a tinted variant of the existing `.race-stat` badge) and `.race-format-badge` (same visual language at table scale, `white-space: nowrap`, wraps on multiple badges per cell). Both use a forest-green tint (`rgba(45, 68, 48, 0.07)` fill, `var(--forest-mid)` text) rather than the neutral `--off-white` of the numeric stats — format is categorical, not a measurement, and the colour separates the two kinds of fact sitting side by side. No new CSS variables.
- Verified end-to-end against production data: `mauerweglauf_berlin/2026` renders four Relay badges in the table and one on the selected race; `marcs_backyard_ultra/2026` renders both `Backyard Ultra` and `Timed` (the multi-label path); `saintelyon/2026` correctly shows table badges but an empty detail stat because the default-selected race (longest distance) has no format; `london_marathon/2026` suppresses the column entirely. Anonymous requests render no format markup at all, since the whole race table is gated.

## [1.4.0] — 2026-08-06

### Changed — Whole tile is now the click target for the event page

- `app/templates/partials/race_tile.html`: the two duplicate `.tile-name-link` anchors (tile face + hover overlay) are replaced by a single stretched `<a class="tile-link">` covering the whole tile, with `aria-label` set to the event name (the anchor is empty, so the label is its accessible name). The event name renders as plain white text on both surfaces — no link styling, since the entire tile is now the affordance and already carries `cursor: pointer`. Being a real anchor, middle-click / Ctrl+click open-in-new-tab and right-click → copy-link work for free.
- Layering: `.tile-hover` creates its own stacking context (`transform` + `opacity`), so overlay buttons could never be z-indexed *above* a stretched link outside it. Inverted instead: `.tile-link` sits at `z-index: 3` (above the tile face at 2), `.tile-hover` moves to 4 and stays `pointer-events: none` even when hovered/revealed — clicks on overlay text/rows fall through to the link beneath. A new rule re-enables `pointer-events: auto` on `a` / `button` inside the overlay only under `.tile:hover` / `.tile--revealed`, so Going / Interested / Change / Remove and the anon "Sign in to join" CTA keep priority over navigation, and are not phantom-clickable while the overlay is invisible. `.tile-terrain-badge` bumped 4 → 5 to stay painted above the overlay.
- `static/css/main.css`: `.tile-name-link` rule family deleted (including the `--link-on-dark` green underline on hover — no longer needed). New `.tile-link` block with a `:focus-visible` inset outline in `var(--accent)` (yellow reads on the dark photo surface).
- `static/js/attendance.js`: no logic change. The mobile first-tap `preventDefault` already blocks the stretched link while revealing, and the `[data-action]` early-return already protects the attendance buttons on the second tap — so first tap reveals, second tap anywhere else on the tile navigates. Comments updated to describe the new mechanism.
- No backend, schema, or dependency change. `partials/race_tile.html` is only included by `index.html`; the event page and profile shelves are untouched.

### Added — Three new dedicated event photos

- `app/imaging/inputs/dedicated/`: three new hand-picked event photos — `road_maraton_san_sebastian.jpg`, `road_kreuzberg_quarter_marathon.jpg`, and `trail_cappadocia_ultra_trail.jpg` (the Cappadocia file was already in the drop folder without a credit; the manifest generator's bidirectional check caught it and its credit was supplied alongside the two new ones).
- `docs/dedicated_credits.md`: three new credit entries appended with the Unsplash-license-compliant `Photo by <a>Name</a> on <a>Unsplash</a>` line (Andrea Huls Pareja, Jonas Tebbe, Timur Garifov). All hrefs quoted, matching the generator's regex.
- `app/imaging/dedicated_manifest.json`: regenerated via `scripts/generate_dedicated_manifest.py` — now 13 entries (was 10). Bidirectional file/credit match confirmed at generation.
- Published and deployed — the workstation `python -m app.imaging --style passthrough --tile-version v02` step and the subsequent `bash scripts/deploy.sh` were run, so the GCS bucket and the app-startup dedicated-slug cache have picked up the three new events.

### Changed — Nav user links condensed into an avatar dropdown menu

- `app/templates/base.html`: the signed-in nav previously rendered three inline links (display name → `/profile`, `Settings`, `Log out`) via `.nav-user` / `.nav-profile` / `.nav-settings` / `.nav-logout`. Replaced by a single `.nav-user-menu` block: a `<button class="nav-avatar-btn">` trigger showing the signed-in user's own avatar (Google photo with `referrerpolicy="no-referrer"` and the site-standard `onerror` fallback to the `--avatar-color-{id % 4}` initial swatch, cloned from the `avatar_strip` macro pattern — deliberately not the `.avatar--stock` "ir" glyph, which means "hidden attendee" site-wide), and a `.nav-dropdown` panel with three `role="menuitem"` links: My profile → `/profile`, Settings → `/settings`, Log out → `/auth/logout`. The button carries `aria-haspopup="menu"`, `aria-expanded` (JS-synced), and `aria-label="Account menu"` since the avatar image alone has no accessible name. Signed-out branch (Google sign-in button) untouched. New `<script src="/static/js/nav.js">` include beside `attendance.js`.
- `static/css/main.css`: old `.nav-user`, `.nav-username` (already unused), `.nav-profile`, `.nav-settings`, `.nav-logout` rules deleted (grep confirmed only `base.html` referenced them). New rule family: `.nav-user-menu` (relative anchor), `.nav-avatar-btn` (reset button chrome, circular, `:focus-visible` ring in `var(--accent)` — yellow reads on the dark nav where forest green would vanish), `.nav-avatar` / `.nav-avatar--initial` (32px circle — slightly larger than the 26px strip avatars so it reads as a control — same white border language, centered 13px initial), `.nav-dropdown` (absolute, right-anchored under the trigger, white card with `var(--border)` / `var(--radius)` / `0 8px 24px` shadow, `min-width: 160px`, `display: none` until the wrapper has `.open`, `z-index: 50` to clear the event hero's layers), `.nav-dropdown-item` (block link, 13px, `var(--forest-mid)` per the links-on-light-surfaces token rule, hover/focus tint `var(--off-white)` + `var(--forest)`), `.nav-dropdown-item--logout` (top border separating the destructive-ish action).
- `static/js/nav.js`: new, ~29 lines, same vanilla idiom as `crews.js`. Click toggles `.open` and `aria-expanded`; outside click closes; Escape closes and returns focus to the button; bails silently when `.nav-user-menu` is absent (signed-out pages). No arrow-key roving focus — Tab order and Escape cover keyboard use for three links; revisit if the menu grows.
- No backend, schema, config, or dependency change — `current_user` (with `avatar_url`, `display_name`, `id`) was already threaded into every template.

### Fixed — Stock tiles silently defaulting to `mixed` for TBC events

- `scripts/backfill_event_image_terrain.py`: new one-shot backfill. `EventImageService._normalize_terrain(None)` returns `mixed`, and `get_or_create_for_events` inserts lazily on first tile render with `on_conflict_do_nothing`, so any event first seen while its source `terrain_type` was still NULL locked in `terrain='mixed'` (and a `mixed_*` stock file) forever — even after the scraper later populated `terrain_type`. TBC occurrences were disproportionately affected (~82% mismatched) because scrapers typically can't classify terrain before the organiser publishes details. Concrete symptom: `comrades_marathon` (source `terrain_type='road'`, `occurrence_status='tbc'`) was serving `mixed_08_canal-side-path`. The script targets stock rows where source `terrain_type` is populated as `road`/`trail`/`mixed` and disagrees with the assigned terrain, picks a fresh stock filename via the same `_pick_stock` used at insert time, and rewrites the three attribution columns to match. Dry-run by default; `--apply` commits. Deliberate exclusions: source=`other` (intentional `other→mixed` mapping), rows currently `trail` whose source now says `mixed` (judged to be scraper regressions, not fixes to propagate), and dedicated slugs (resolver bypasses `stock_filename` for those). Ran once — 71 unique `web.event_images` rows updated (out of 262 non-unique candidate rows spanning current / tbc / upcoming; MV join returns one row per race distance, script de-dupes). 8 events remain mismatched because their races within the same event carry conflicting terrain values in the MV; that's a data-shape limit of one image per event, not a bug in the backfill.
- **Recurrence hole still open by design.** The `_normalize_terrain(None) → 'mixed'` default in `app/services/event_image_service.py` is unchanged, so a new event first rendered while its source terrain is still NULL will silently default to `mixed` again. Rerun the backfill periodically, or revisit the default when ready. Not touched to preserve existing insert-time behaviour.

## [1.3.0] — 2026-07-31

### Changed — Point Race model at the upcoming-only view

- `app/models/core.py`: `Race.__tablename__` swapped from `mv_denormalized_event_data` to `v_denormalized_event_data_upcoming`. The view lives in `core` and is owned by indie-runners-scraper; it filters the MV down to rows that actually belong to the current occurrence (per-race edition gate), so stale prior-edition races no longer attach to new TBC / upcoming occurrences. Concrete symptom fixed: `gran_raid_guillestrois` was showing all 10 historical races on the 2027 event page after the fresh scrape, even though only `ultra_tour` had 2027 data — the other 9 rode along on migration 029's widened `EXISTS` gate + LATERAL fallback. Deploy coordination: the view must exist in the DB before this deploys or every page 500s on the first query.

### Fixed — TBC events sorting to top of zero-engagement bucket

- `app/main.py`: the `races.sort` tiebreaker at the end of `index()` no longer keys on `r.race_date or date.max`. Migration 029 (scraper) added a LATERAL prior-edition fallback on `core.mv_denormalized_event_data`, which populates `race_date` on TBC rows with the previous edition's date (e.g. a 2026-04-10 date on a row whose `occurrence_year` is 2027). The old tiebreaker relied on the coincidence that TBC rows had `NULL race_date` and therefore sorted last via `date.max`; that coincidence no longer holds, so TBC events with zero engagement were leapfrogging dated events with zero engagement. New tiebreaker uses `r.is_tbc` + `r.expected_year` + `r.expected_month` (first-of-month; December if month is null) so TBC and dated events interleave by their best-known expected date, matching the DB query's `COALESCE(race_date, make_date(...))` ordering convention.

### Added — Two new dedicated event photos

- `app/imaging/inputs/dedicated/`: two new hand-picked event photos added — `trail_13_valleys_ultra.jpg` and `road_barcelona_half_marathon.jpg`.
- `docs/dedicated_credits.md`: two new credit entries appended with the Unsplash-license-compliant `Photo by <a>Name</a> on <a>Unsplash</a>` line. The 13 Valleys credit block ships from Unsplash with unquoted `href=…` attributes; both entries normalized to `href="…"` so `scripts/generate_dedicated_manifest.py` parses them (its regex requires quoted attributes).
- `app/imaging/dedicated_manifest.json`: regenerated via `scripts/generate_dedicated_manifest.py` — now 10 entries (was 8). Bidirectional file/credit match confirmed at generation.
- Publish and Cloud Run redeploy pending — the workstation `python -m app.imaging --style passthrough --tile-version v02` step and the subsequent `bash scripts/deploy.sh` are user-run so the GCS bucket and the app-startup dedicated-slug cache pick up the two new events.

### Changed — Image publish workflow trimmed to the single live version

- `docs/IMAGING.md`: the *Adding a stock photo* step 5 and *Adding a dedicated photo* step 4 previously instructed publishing all three tile versions (`v01` duotone, `v02` passthrough, `v03` grade) on every new photo. Only `v02` is served — `app/config.py` sets `tile_version = "v02"` and `scripts/deploy.sh` does not override it — so the other two prefixes were wasted work. Both steps now publish `--tile-version v02` only. The *Side-by-side comparison workflow* section is reworded from "the default flow" to "an opt-in step when evaluating a candidate styler". No code change; documentation only.

## [1.2.0] — 2026-07-28

### Added — Actual race dates and date ranges on tiles

- `app/services/race_service.py`: new module-level `format_date_range(start, end)` helper that produces `"15 Aug 2026"` for single-day, `"15 – 16 Aug 2026"` for same-month spans, `"31 Aug – 2 Sep 2026"` for cross-month spans, and `"31 Dec 2026 – 2 Jan 2027"` for cross-year spans. `RaceService.list_races` grouping loop now also tracks `race_date_end = max(race_date)` per event across its N race rows, and populates `race_date_display` on each tile via the formatter. Multi-day events like Spartathlon and Transgrancanaria now read honestly as spans instead of collapsing to their first race's date.
- `app/schemas/race.py`: `EventListItem` gains `race_date_end: Optional[date] = None` and `race_date_display: Optional[str] = None`. Both defaulted so nothing breaks.
- `app/templates/partials/race_tile.html`: tile face date line and hover-panel Date row both read `race.race_date_display`, replacing the previous `race_date.strftime('%b %Y')` ("Aug 2026") tile face and the previous `race_date.strftime('%-d %b %Y')` hover row. Both now show the exact date or span.

### Added — Five new dedicated event photos

- `app/imaging/inputs/dedicated/`: five new hand-picked event photos added (spartathlon, athens_authentic_marathon, london_marathon, tenerife_bluetrail, transgrancanaria). Renamed `mixed_spartathlon.jpg#` (stray shell-escape suffix) to `mixed_spartathlon.jpg` so `scripts/generate_dedicated_manifest.py` accepts it.
- `docs/dedicated_credits.md`: five new credit entries appended, each with the Unsplash-license-compliant `Photo by <a>Name</a> on <a>Unsplash</a>` line.
- `app/imaging/dedicated_manifest.json`: regenerated via `scripts/generate_dedicated_manifest.py` — now 8 entries (was 3). Bidirectional file/credit match confirmed at generation.
- Published to all three live tile versions (`v01` duotone, `v02` passthrough, `v03` grade) via `python -m app.imaging`; 5 new dedicated WebPs land on the public GCS bucket alongside the existing 3. Verified via `curl -I` — all 5 return HTTP 200. Cloud Run deploy required to pick up the new slug set on startup and rewrite attribution rows.

### Changed — Hero eyebrow copy

- `app/templates/index.html`: hero eyebrow reads `Your running community · Indie races · For runners, by runners` (was `... · Global races · ...`). Reflects the actual site scope — European races today, "indie" as a positioning word — rather than the aspirational "global".

### Changed — Logo is now a link back to home

- `app/templates/base.html`: `.logo` div wrapped in `<a href="/" class="logo-link">` so the Indie Runners wordmark + tagline navigate back to `/` from every page that extends `base.html` (event, profile, settings, imprint, privacy, terms, crews — all of them).
- `static/css/main.css`: new `.logo-link` rule kills the default anchor underline (base + `:hover / :focus / :visited`) and forces `color: inherit`; explicit `text-decoration: none` on the two child spans defends against browsers painting the underline through descendants. `display: inline-block` so the anchor bounding box matches the logo geometry.

### Changed — Anon sign-in CTAs on the event page switched from green to yellow

- `app/templates/event.html`: both anon sign-in CTAs on the event page — the action-bar "Sign in to join" and the locked-panel "Sign in to see race details" — swapped from `.attendance-btn--going` (green, the mark-attendance colour) to a new `.attendance-btn--signin` (yellow, matching the tile hover CTA). Signed-in Going / Interested buttons remain green; only the anon prompts change.
- `static/css/main.css`: new `.attendance-btn--signin` modifier — `background: var(--accent)`, `color: var(--text-dark)`, hover `background: var(--accent-light)`. Reuses the existing `--accent` / `--accent-light` tokens; no new colour variables.

### Removed — Redundant anon "Sign in to see who's going/interested" links

- `app/templates/event.html`: the two `<a class="whos-coming-signin-link">` links inside the anonymous Who's-coming section were removed. The column titles + silhouette avatars already imply the affordance, and the primary sign-in CTA (yellow, in the action bar) plus the secondary one (yellow, in the locked panel) both carry the ask. The `.whos-coming-signin-link` CSS class remains for now — cheap to leave in place.

### Changed — Tile hover CTA padding and alignment

- `static/css/main.css`: `.hover-cta` gains `padding: 9px 14px` (was `9px 0`) and `text-align: center`. The full-width Sign-in-to-join / Going / Interested buttons on the tile hover overlay now have horizontal breathing room and read as visually-centered rather than flush-left with a trailing arrow anchored to the right edge. Applies transitively to `.hover-cta--going` and `.hover-cta--interested` since they inherit the base rule.

### Changed — More space between avatar cluster and count on tile face

- `static/css/main.css`: `.tile-attendees` gap bumped from `6px` to `12px`. The going-count / interested-count label on the tile face now has more visual separation from the overlapping avatar circles. Applies to both Going and Interested rows since they share the class.

### Added — TBC event occurrences surfaced on tiles, event page, and profile

- `app/models/core.py`: `Race` mapping gains two columns projected by the rebuilt MV in the scraper repo (migration 025 there): `occurrence_status` (Text) and `occurrence_expected_month` (Text — the MV projects everything as text, matching the existing `occurrence_year` pattern; both get cast to Integer at query time when used in `make_date` / `COALESCE` arithmetic). Read-only mapping change, no migration in this repo.
- `app/services/race_service.py`: new `format_tbc_expected(year, month)` helper next to the existing `format_date_range` — returns `"October 2027 (TBC)"` when the expected month is set, `"2027 (TBC)"` when only the year is set, `"TBC"` as a defensive fallback. `list_races` gains a `sort_key = COALESCE(race_date, make_date(occurrence_year::int, COALESCE(occurrence_expected_month::int, 12), 1))` local, used three times: the WHERE clause is now `or_(confirmed_branch, tbc_branch)` where the TBC branch requires `occurrence_status = 'tbc'` and the expected month-start is not in the past; the optional `date_from` / `date_to` filters compare against the coalesced key (so a user filtering to "October 2027" gets both real-October races and TBC-expected-October races); the `ORDER BY` uses the same coalesced expression. Grouping loop captures `is_tbc`, `expected_month`, `expected_year` on first-see of each event. `EventListItem` construction chooses `format_tbc_expected` when `is_tbc`, else `format_date_range`. Confirmed events are untouched.
- `app/schemas/race.py`: `EventListItem` gains `is_tbc: bool = False`, `expected_month: Optional[int] = None`, `expected_year: Optional[int] = None`. All defaulted so existing constructors keep working.
- `app/templates/partials/race_tile.html`: outer `.tile` gets a `tile--tbc` class when `race.is_tbc`. The "Registration open" hover badge is suppressed for TBC (no `race_status` on TBC rows so this would never fire anyway, but explicit `and not race.is_tbc` guard so the intent is obvious). The hover panel's `.hover-rows` block is TBC-aware: Date and Country rows always render (Date carries the "October 2027 (TBC)" string, Country is stable across editions), while Distances / Location / Entry-fee are dropped in favour of one muted italic notice — *"Race details will be confirmed closer to the date."* Attendance CTAs (Going / Interested / Sign in to join) unchanged on TBC tiles — RSVP is allowed because `occurrence_id` is stable across the backend's in-place TBC → upcoming flip.
- `static/css/main.css`: new `.hover-tbc-notice` (italic, 12px, `rgba(255,255,255,0.65)` — same muted tier as `.hover-row-val` but lower opacity) and `.tile--tbc .tile-terrain-badge { opacity: 0.55 }` (dims the Trail / Road / Mixed badge since it carries less signal on an unconfirmed edition). Hero image is deliberately NOT dimmed — the photo remains the tile's visual anchor and should stay crisp regardless of edition status.
- `app/main.py` `event_detail`: derives `is_tbc`, `expected_year`, `expected_month` from the resolved occurrence's first row, computes `tbc_display` via the same `format_tbc_expected` helper the index route uses, threads all four into the `event` dict in template context. Import updated to expose `format_tbc_expected` alongside the existing `RaceService` / `RaceFilters` symbols.
- `app/templates/event.html`: hero meta line renders `event.tbc_display` instead of the occurrence start–end range when the occurrence is TBC. Signed-in body wraps the race-selector + race-detail sections in `{% if event.is_tbc %}<notice card>{% else %}<sections>{% endif %}`. The notice card reuses the existing `.locked-panel` styling with copy tweaked to *"This edition is not yet confirmed"* plus an explanation of what will land here later; if the event has an `event_website_url`, the notice includes a yellow "Visit the official website →" CTA (same `.attendance-btn--signin` styling as the sign-in CTAs, so the visual language of "the load-bearing action here" is consistent). Anon locked-panel path is unchanged — its existing "Sign in to see race details" CTA still makes sense for a TBC event (details will exist post-confirmation; sign-in is the site-wide anon nudge either way). Who's-coming section is unchanged — TBC events accept RSVPs so the participant list should render as usual.
- `app/services/profile_service.py`: `is_upcoming(row)` at line 70 now returns `True` when `row.race_date IS NULL` (previously returned `False`). A TBC RSVP snapshotted at mark time (per Slice B decision, we store NULL rather than inventing a placeholder date) is by definition forward-looking, so it belongs in `going_upcoming` / `interested`, not `going_past`. Sort keys already handled NULL via `date.max` / `date.min` fallbacks so no change there. `AttendanceService.mark_attendance` was already NULL-safe (log line even names the case), and `AttendanceService.clear_attendance` delete guard was already NULL-safe via an explicit `is not None` check — no changes needed.
- No migration in this repo. Backend migration 025 (scraper repo) is the prerequisite: it added `expected_month SMALLINT` to `core.event_occurrences`, widened the status CHECK constraint to allow `'tbc'`, and rebuilt `core.mv_denormalized_event_data` to project the two new columns and include TBC rows under a widened status filter (`IN ('upcoming', 'current', 'tbc')`). After the first mint run against production there were 79 TBC occurrences visible in the MV as ~423 rows.
- `docs/ARCHITECTURE.md`: brief note under Tables owned by this service that `web.attendance.race_date` may be NULL for TBC RSVPs and that `ProfileService.is_upcoming` treats NULL as upcoming.

## [1.1.0] — 2026-07-27

### Added — GoatCounter analytics (cookieless, GDPR-exempt)

- `app/templates/base.html`: single async `<script data-goatcounter="https://indierunners.goatcounter.com/count" src="//gc.zgo.at/count.js">` added inside `<head>` immediately before `{% block head %}`, so every page that extends the base template gets it — no per-page wiring, no middleware, no backend change.
- `app/templates/privacy.html`: section 5 rewritten. The old "Google Analytics — planned, not yet active" placeholder is replaced by an "Analytics" section that names GoatCounter, links to `https://www.goatcounter.com/`, enumerates what is collected (visits, page views, referrers, browser type, country), documents the 8-hour session-scoped repeat-load window, the 365-day retention, and the no-cookie / no-third-party-sharing guarantees. Section numbering (`<h2>5.`) and CSS classes are unchanged.
- `docs/ARCHITECTURE.md`: the pre-shipping "Analytics planned, not yet active" caveat under Legal pages is replaced by a description of the current GoatCounter integration and the conditions under which section 5 would need rewriting again (any tool that sets cookies or identifies individuals).
- No Python, no migration, no config, no new dependency, no session or middleware change. Cookieless by design, so no consent banner is added.

## [1.0.1] — 2026-07-27

### Added — Terms of Use page

- `app/main.py`: adds `GET /terms` route. Anon-accessible and threads `current_user` through so the nav still reflects signed-in state. Follows the codebase's positional `TemplateResponse(request, name, ctx)` convention used by the sibling `/imprint` and `/privacy` handlers.
- `app/templates/terms.html`: new. Twelve numbered sections covering identity (with cross-links to imprint and privacy), scope of service, eligibility and Google-only sign-in, best-effort race data with the "confirm with organizer" disclaimer, third-party link disclaimer, crews and invite-link responsibility, acceptable use, ownership of user-added display name / avatar / crew names, termination via email to `paulo@indierunners.co`, "as is" disclaimer plus German-law liability limits (with the mandatory carve-out for intent / gross negligence / life-body-health), change-notification via the "last revised" date, and German governing law with the EU-consumer carve-out. Reuses the existing `legal-page` / `legal-lede` / `legal-footnote` CSS classes from the imprint and privacy pages — no new styles. Carries a Jinja maintainer comment at the top reminding to bump the "Last revised" date whenever the terms are changed.
- `app/templates/base.html`: footer gains a `Terms` link after the existing `Imprint` and `Privacy` links, so all three legal surfaces are reachable within one click from every page, signed-out included.

## [1.0.0] — 2026-07-27

### Added — Canonical apex domain and legacy host redirects

- `scripts/deploy.sh`: `GOOGLE_REDIRECT_URI` env var flipped from `https://beta.indierunners.co/auth/google/callback` to `https://indierunners.co/auth/google/callback`. Google OAuth Client's Authorized Redirect URIs list was updated in Cloud Console (Credentials, not consent screen) in the same window to hold all three callback URLs (apex, www, beta) so sign-in works during and after rollout — beta can be removed from the OAuth client once no traffic hits the beta host.
- `app/main.py`: new `CanonicalDomainMiddleware` (`BaseHTTPMiddleware`) 302-redirects `beta.indierunners.co` and `www.indierunners.co` to `indierunners.co`, preserving path + query. 302 (not 301) during rollout so a rollback is not cache-locked in browsers; promote to 301 once stable. Registered *after* `SessionMiddleware` in source order — Starlette's `add_middleware` prepends, so last-added is outermost, meaning non-canonical hosts short-circuit before any session, DB or template work.
- `Dockerfile`: uvicorn CMD gains `--proxy-headers --forwarded-allow-ips='*'` so `X-Forwarded-Proto` from Google Frontend is honoured. Without this, `request.url.scheme` inside the container is `http` and every absolute URL built from `request.url` (the canonical-host redirect target, `request.url_for` for crew invite links at `main.py:555`, the `post_login_redirect` session stash at `main.py:602`) leaks an `http://` scheme. Trusting `*` is safe on Cloud Run — the container is only reachable via Google Frontend, no direct public ingress path exists — but this pattern must not be copied to any service with direct ingress.
- `docs/ARCHITECTURE.md`: `GOOGLE_REDIRECT_URI` prod value updated; Deployment section rewritten to list all three custom domain mappings, document the middleware's ordering rationale, and record the `--proxy-headers` scheme-trust decision. No schema, no migration, no data change.

### Added — Who's coming participant list on the event page (Phase 3)

- `app/services/attendance_service.py`: dropped the `if len(...) < 4` cap on both the going and interested branches of `get_attendance_summary`. `going_users` and `interested_users` now hold every visible attendee, not just the first four. The action bar strips still trim display to 4 via the shared `avatar_strip` macro's `cap` argument; the overflow chip arithmetic is `total - shown`, so a summary with 20 interested and 4 shown now reads `+16` instead of the pre-uncap `+16` (behaviour identical for anon since the identity list was already empty). `going_count` / `interested_count` and `going_hidden_count` / `interested_hidden_count` are computed in outer branches and are unaffected. No signature change on `get_attendance_summary` and no field change on `AttendanceSummary`.
- `app/templates/event.html`: new `<section class="whos-coming">` inside `.event-body`. Signed-in path sits after the closing `</section>` of `.race-detail` inside the existing `{% if current_user %}` gate. Anon path sits as a sibling of `.locked-panel` inside the `{% else %}` branch. Both variants are wrapped in `{% if attendance_summary.going_count > 0 or attendance_summary.interested_count > 0 %}` so an event with no attendees renders no Who's-coming section at all; each column is additionally gated on its own count so single-status events do not render an empty second column.
- Signed-in section: two columns (Going, Interested), each an `<ul class="whos-coming-list">` iterating `attendance_summary.going_users` / `.interested_users`. Every row is `<img class="avatar">` (Google avatar with `referrerpolicy="no-referrer"` matching every other avatar site-wide) or a `.avatar.avatar--initial` fallback using the same `--avatar-color-{id % 4}` inline style the shared macro uses, plus `<a href="/profile/{u.id}" class="whos-coming-name">`. When `going_hidden_count` / `interested_hidden_count` is greater than zero, a `<p class="whos-coming-others">and N other(s)</p>` line renders under the list — worded identically whether the hidden attendees are `private` or `crews_only`-blocked so the reason never leaks. Singular / plural aware.
- Anon section: same two-column shell (`.whos-coming.whos-coming--anon`), each column calls `avatar_strip([], count, count, 4)` for the shared "ir" silhouette treatment plus `+N` overflow past cap, and renders a `<a class="whos-coming-signin-link" href="/auth/google?next={{ request.url.path }}">Sign in to see who's going</a>` (interested variant reads `who's interested`). The `next` value routes through the Phase 2 `_validate_next` helper and the `post_login_redirect` session key with no change on either side.
- `static/css/main.css`: new class family `.whos-coming` (section wrapper), `.whos-coming-cols` (two-column grid `1fr 1fr` with `2rem` gap), `.whos-coming-col` (white card matching `.detail-card`), `.whos-coming-col-title` (Fraunces 1.15rem, weight 500, `var(--forest)`), `.whos-coming-list` / `.whos-coming-row` (flex-column list, `0.5rem` gap; each row flex-row with `0.6rem` gap), `.whos-coming-name` (`var(--forest-mid)`, hover underline), `.whos-coming-others` (italic `var(--text-mid)`, top margin), `.whos-coming-anon-row` (silhouette flex row), `.whos-coming-signin-link` (inline underline `var(--forest-mid)`, hover `var(--forest)`). Existing `<= 620px` media query extended with `.whos-coming-cols { grid-template-columns: 1fr; gap: 1rem; }` and `.whos-coming-col { padding: 1.25rem; }` so columns stack cleanly on mobile. No new colour variables; no change to `.locked-panel`, `.race-selector`, `.race-detail`, `.event-action-bar` or any Phase 1 / Phase 2 rule.
- No JS change. `static/js/attendance.js` still updates the action-bar strip and counts on mark / remove; the Who's-coming section refreshes on the next page load (accepted staleness — the viewer's own attendance change is already reflected in the action bar). No migration, no schema change, no new dependency.

## [0.16.0]

### Added — Anonymous gating on the event page (Phase 2)

- `app/main.py`: new module-level helper `_validate_next(raw)` returns the raw string only when it starts with a single `/`, is not protocol-relative (`//`), does not start with `http:` / `https:` / `data:` / `javascript:` (case-insensitive), contains no `\r` / `\n` / `\t` / `\` (the backslash reject closes a browser-normalisation bypass — `/\evil.com` becomes protocol-relative in several parsers) and no leading or trailing whitespace. Everything else returns `None`. Plain-English log line `rejecting unsafe next redirect` fires when a non-empty input is rejected.
- `app/main.py`: `google_login` handler gains `request: Request, next: Optional[str] = None`. When `_validate_next(next)` returns a string, it is stashed into `request.session["post_login_redirect"]` before the redirect to Google. The existing `google_callback` (main.py:663) already pops and honours that key with a fallback to `/`, so no change was needed on the callback side. Reuses the same session key that `crews_join_form` already uses — no `state` round-trip and no second key to maintain.
- `app/templates/event.html`: the anon attendance-bar CTA becomes `<a href="/auth/google?next={{ request.url.path }}">`. No change to the avatar strip — signed-out viewers keep the existing `.avatar--stock` "ir" glyph that the `partials/avatar_strip.html` macro already renders for hidden attendees, matching every other privacy tier across the site (tiles, hover overlays, JS mark/remove refresh). BRIEF's suggested `.avatar--placeholder` variant is not needed; recycling the existing glyph keeps the site consistent with no duplicate work.
- `app/templates/event.html`: the entire `<section class="race-selector">…</section>` and `<section class="race-detail">…</section>` block — race table, detail cards, and the elevation placeholder that sits inside `.race-detail` — is wrapped in a single `{% if current_user %} … {% else %} <locked panel> {% endif %}`. Anonymous responses render only the locked panel in that slot; no distance, ascent, price, cutoff, registration or elevation-placeholder markup is written into the HTML source at all.
- `app/templates/event.html`: locked panel is one white card with a title `See the full race lineup`, body `Distances, climb, prices, cutoffs and registration status for every race at this event. Free once you sign in.`, and a `Sign in to see race details` button styled with `.attendance-btn attendance-btn--going locked-panel-cta` linking to `/auth/google?next={{ request.url.path }}`. Both anon CTAs — the attendance-bar one and the locked-panel one — point at the same URL, so click-through behaviour is uniform.
- `static/css/main.css`: adds `.locked-panel` (white card, `1px solid var(--border)`, `var(--radius)`, `2.5rem 2rem` padding, centred flex column, `1rem` gap), `.locked-panel-title` (Fraunces 1.5rem, weight 500, `var(--forest)`), `.locked-panel-body` (`44ch` max-width, `var(--text-mid)`, line-height 1.55, `margin: 0`), `.locked-panel-cta` (`min-width: 220px` + `:focus-visible` outline `2px solid var(--forest)` with `offset: 3px` for a visible keyboard focus ring). Mobile at `<= 620px` tightens `.locked-panel` padding to `2rem 1.25rem` and makes the CTA full-width. No new colour variables; no change to any `.event-hero*`, `.event-action-bar`, `.detail-card` or `.race-selector` rule from 0.15.0.
- No JS change. `static/js/attendance.js` still builds avatar strips with `.avatar--stock` in mark/remove responses; that code path is only reached for signed-in viewers, and the plain-stock path is never emitted by JS in the anon flow. No migration, no schema change, no new dependency.
- Regression note: `curl -sS <event URL>` for a signed-out visitor should return 200 with the hero, counts and locked panel, and match `-c 'locked-panel'` at least once while matching zero of `race-table|race-detail|elevation-placeholder|km|ascent|cutoff|registration`. Signed-in cURL still contains all of the above.

## [0.15.0]

### Added — Event page hero image and photographer credit (Phase 1)

- `app/main.py`: `event_detail` now resolves the tile image for the single event by reusing `EventImageService.get_or_create_for_events` with a one-item list (no new resolver method, per BRIEF's "do not duplicate the resolver"), then calls `resolve_tile_image(event_slug, event_image, request.app.state.dedicated_slugs)` — same startup cache the index route reads. Passes `tile_image_url` and `tile_attribution` into the template context. Both default to `None` if the event has no `event_id`, no image row, or no `event_slug`. Plain-English log line `resolving hero image for event page` (no exclamation marks, per BRIEF Shared Conventions).
- `app/templates/event.html`: header restructured. The old white-card `<header class="event-header">` (title + meta + attendance stacked in one block) is replaced by a `<header class="event-hero">` that contains an optional `<img class="event-hero-photo">` (guarded on `tile_image_url`, `alt=""`, `loading="eager"`, `fetchpriority="high"`, `referrerpolicy="no-referrer"` to match the Google-avatar ORB pattern from 0.12.0), an optional `<span class="event-hero-credit">Photo · {{ tile_attribution }}</span>` (plain text, no anchor — `attribution` is a bare `VARCHAR(255)` with no URL column, so a link isn't possible today), and an `.event-hero-inner` wrapping the existing type badge / title / meta / website link unchanged. The attendance widget moves out into a sibling `.event-action-bar` card between the hero and `.event-body`; the `.event-attendance` internal markup (avatars, counts, buttons, `data-event-id` / `data-occurrence-id`) is untouched so `static/js/attendance.js` keeps working without change. This phase locks the final header layout — Phase 2 will only modify the avatar row inside `.event-action-bar`, not restructure the hero.
- `static/css/main.css`: swapped the `/* EVENT HEADER */` block for `/* EVENT HERO */`. New rules: `.event-hero` (relative, `overflow: hidden`, `min-height: 340px`, `background: var(--forest)` fallback for broken images), `.event-hero-photo` (absolute-inset `object-fit: cover`, `z-index: 0`), `.event-hero::after` (dark gradient overlay `rgba(0,0,0,0.10) → 0.20 → 0.78`, matches the tile treatment in `.tile::after`), `.event-hero-inner` (relative `z-index: 2`, `padding: 2rem 2.25rem`), `.event-hero-credit` (top-right pill, `rgba(0,0,0,0.32)` bg + `rgba(255,255,255,0.82)` text, `backdrop-filter: blur(3px)`, `z-index: 3`). `.event-title`, `.event-meta`, `.event-meta-sep`, `.event-website-link`, `.event-type-badge` recoloured for the on-dark surface (white / rgba white, modest `text-shadow` on the title, translucent badge with `backdrop-filter`). New `.event-action-bar` white card matching the `.detail-card` / `.race-selector` treatment. Reuses existing tokens only (`--forest`, `--radius`, `--border`); no new colour variables. Mobile media query moved to `<= 620px` and updated for the new hero: reduced `min-height`, tighter inner padding, tighter action-bar padding; stale `.event-header*` mobile rules dropped since the classes no longer exist.
- No JS change. No change to `/` or `/profile/*`.

### Added — Photographer credit populated from stock and dedicated manifests

- `migrations/013_event_image_attribution.sql`: adds `attribution_name`, `attribution_url`, `attribution_source_url` to `web.event_images` (all `VARCHAR(500)`, nullable, no defaults, no CHECK). Additive against the populated 129-row table; existing rows land with the new columns as NULL, which the template's `{% if tile_attribution_name %}` guard tolerates cleanly. The existing single `attribution` column is left in place for backward compatibility — a follow-up PR can drop it after the three-column form has been observed in place, per the migration safety rule "split backfill from delete".
- `app/models/web.py`: `EventImage` gains the three fields matching the migration.
- `scripts/generate_dedicated_manifest.py`: new. Symmetric to `generate_stock_manifest.py`. Parses `docs/dedicated_credits.md` into a `{event_slug, title, photographer_name, photographer_url, photo_url}` list, cross-references filenames in `app/imaging/inputs/dedicated/` (terrain prefix stripped), aborts with a plain warning on mismatch, writes `app/imaging/dedicated_manifest.json`.
- `app/imaging/dedicated_manifest.json`: new, generated, 3 entries covering `berlin_marathon`, `berlin_half_marathon`, `mauerweglauf_berlin`.
- `app/imaging/dedicated_manifest.py`: new. `load_manifest`, `validate_entry`. Mirrors `stock_manifest.py`, except a missing manifest returns `[]` rather than raising — the file is generated and not required for the app to boot when no dedicated photos exist yet.
- `scripts/backfill_event_image_attribution.py`: new, one-shot. Iterates every `web.event_images` row; for rows whose `event_slug` is in the dedicated manifest, writes the dedicated credit; else looks up `stock_filename` in the stock manifest and writes the stock credit. Idempotent — reruns overwrite with the same values. Prints per-source counts and lists un-matched rows; exits non-zero if any row could not be matched. User runs it (migration approval convention applies to any DB write).
- `app/services/event_image_service.py`: `get_or_create_for_events` now populates `attribution_name`, `attribution_url`, `attribution_source_url` in the insert dict, sourced from the stock manifest slot picked at assignment time. Every new event lands with credit already written. New `refresh_dedicated_attributions(dedicated_slugs)` method walks rows whose `event_slug` is dedicated and (re)writes the three attribution columns from the dedicated manifest, skipping rows already in the target state — idempotent, safe to call on every boot. Also loads the dedicated manifest once at module import into `_DEDICATED_BY_SLUG`.
- `app/main.py`: the FastAPI startup hook now calls `EventImageService(db).refresh_dedicated_attributions(app.state.dedicated_slugs)` right after `load_dedicated_slugs()` populates the cache. Logs `Refreshed dedicated attributions on N rows` when any row is updated. Event detail route swaps the single `tile_attribution` for the three fields (`tile_attribution_name`, `tile_attribution_url`, `tile_attribution_source_url`) in both the resolution block and the template context.
- `app/templates/event.html`: hero credit is now a two-branch conditional. All three fields set → `<span class="event-hero-credit">Photo by <a>{name}</a> on <a>Unsplash</a></span>` with `target="_blank" rel="noopener noreferrer"` on both anchors (Unsplash license compliance: profile + photo page). Name only → plain-text `Photo · {name}`. No name → no pill (unchanged graceful degradation).
- `static/css/main.css`: `.event-hero-credit` gains a `max-width: calc(100% - 20px)` guard for long attributions, padding bumped to `3px 10px`. New `.event-hero-credit a` rule — colour inherits, subtle `rgba(255,255,255,0.35)` bottom border that lifts to `0.75` on hover.
- `docs/IMAGING.md`: new "Photographer credits" section documenting the two manifests + the automatic write-on-assign + startup-refresh + backfill flow. "Adding a stock photo" step 4 notes automatic credit propagation for new events + points at the backfill script for sweeping already-assigned events. "Adding a dedicated photo" gains a new step 2 (credit entry in `docs/dedicated_credits.md`) and step 3 (regenerate the dedicated manifest); step 5 explains the startup refresh now writes attribution as a side effect. Local layout listing updated to include the two new manifest files and the new script.

## [0.14.0]

### Added — Imprint and Privacy Policy pages (§ 5 DDG + GDPR compliance)

- `app/main.py`: adds `GET /imprint` and `GET /privacy` routes. Both are anon-accessible and render plain semantic templates; `current_user` is threaded so the nav still renders the signed-in state when applicable. Calls follow the codebase's positional `TemplateResponse(request, name, ctx)` convention (the dict-with-`request`-key form raises under the installed Starlette version).
- `app/templates/imprint.html`: new. § 5 DDG legal notice with the confirmed Online-Impressum address (Europaring 90, 53757 Sankt Augustin) and `paulo@indierunners.co` as the sole contact channel. Email-only contact is legally sufficient post-CJEU Amazon EU; no phone / contact form. English content, German legal citation kept as-is.
- `app/templates/privacy.html`: new. Sections covering data controller, per-source data inventory (Google OAuth, attendance, session cookie, server logs — pulled from the actual schema, not boilerplate), legal bases (Art. 6(1)(b) + 6(1)(f)), processors (Google + GCP `europe-west1`), the EU-US transfer wording (Google's EU-U.S. DPF certification supplemented by SCCs per Commission Implementing Decision (EU) 2021/914 — verified against `policies.google.com/privacy/frameworks` on 2026-07-22), a "Google Analytics — planned, not yet active" placeholder that explicitly disclaims current tracking, retention ("until deletion is requested" — no automatic expiry), the standard GDPR rights list with a generic "your local data protection authority" complaint pointer, and deletion instructions pointing at `paulo@indierunners.co` with a 30-day response window. No cookie consent banner because no non-essential cookies are set today; this is called out as a dependency of the Analytics rollout, not a surprise.
- `app/templates/base.html`: footer gains `Imprint` and `Privacy` links so both are reachable within one click from every page, signed-out included.
- `static/css/main.css`: adds a `.legal-page` scope with Fraunces headings, prose-friendly max-width, `.legal-lede`, and `.legal-footnote` styles. Scoped to the two legal templates; no overlap with existing utility classes.

### Removed — Slack and early-access links from the footer

- `app/templates/base.html`: removed the `Join our community on Slack` and `Get early access` footer links. Footer now carries only the copyright line plus the new `Imprint` and `Privacy` links, matching the legal-page focus of the footer surface.

## [0.13.0]

### Added — Crews and `crews_only` visibility tier (privacy PR3)

- `migrations/010_crews.sql`: creates `web.crews` (`id`, `slug UNIQUE`, `display_name`, `created_at`, `created_by`) + `idx_crews_created_by`. `created_by` is a soft ref to `web.users.id`, same idiom `web.attendance` uses for `core.events`.
- `migrations/011_crew_memberships.sql`: creates `web.crew_memberships` with composite PK `(crew_id, user_id)`, both FKs cascade on delete, `role` CHECK `IN ('admin','member')` default `'member'`, `idx_crew_memberships_user`. PR3 ships one admin (the creator) per crew; the column exists so PR4 can add co-admins without a schema change.
- `migrations/012_crew_invites.sql`: creates `web.crew_invites` (`id`, `crew_id` FK cascade, `token VARCHAR(64) UNIQUE`, `created_by`, `created_at`, `revoked_at`) + `idx_crew_invites_crew_id`. `token` is a `secrets.token_urlsafe(32)` value (~43 chars). Active-vs-revoked is `revoked_at IS NULL`; rotation = UPDATE old + INSERT fresh.
- `app/models/web.py`: adds `Crew`, `CrewMembership`, `CrewInvite` models mirroring the migrations. `Crew.memberships` / `Crew.invites` relationships use `cascade="all, delete-orphan"` to mirror the DB cascade.
- `app/services/crew_service.py`: new. `CrewService` owns `create_crew` (inserts crew + admin membership + fresh invite in one commit — a brand-new crew has a live URL immediately, per BRIEF Decision 5), `get_crew_by_slug`, `list_crews_for_user`, `is_member`, `is_admin`, `list_members` (admin first), `shares_crew_with`, `get_viewer_crew_ids`, `get_attendee_crew_ids` (bulk, one query, only invoked when the viewer has ≥1 crew AND ≥1 `crews_only` attendee is in the summary), `active_invite_for_crew`, `rotate_invite` (admin-guarded), `find_crew_by_invite_token`, `add_member` (idempotent). Slug helper lowercases + collapses non-`[a-z0-9]+` to `-`; collisions retry with `-2`, `-3`, ... up to 10 before raising.
- `app/services/attendance_service.py`: `get_attendance_summary` signature gains `viewer_crews: set[int] | None = None`. `_is_identity_visible` now takes `viewer_crews` + `attendee_crews`; the `crews_only` branch becomes `bool(viewer_crews & attendee_crews)`. Attendee crew sets are resolved in one bulk query, guarded so no round trip fires when the viewer has zero crews or no `crews_only` attendee is present. Two queries max per summary call regardless of N attendees.
- `app/services/profile_service.py`: `get_profile` gains `viewer_crews: set[int] | None = None`. `_can_view` `crews_only` branch fetches the target's crew set (one scalar lookup) and returns `bool(viewer_crews & target_crews)` — only runs when the target's visibility is `crews_only`, so the public-target path pays nothing.
- `app/services/settings_service.py`: `_SELECTABLE_LEVELS` becomes `{'public', 'crews_only', 'private'}`. `crews_only` is now a valid POST value and writes the column.
- `app/main.py`: adds route family `GET /crews/new`, `POST /crews/new` (400 on invalid name, PRG 303 to `/crews/{slug}?created=1` on success), `GET /crews/{slug}` (member-gated — non-member and non-existent both render `crews_hidden.html` with no crew name surfaced, per PLAN Decision 10), `POST /crews/{slug}/invite/rotate` (admin-only, 403 for non-admin members, 404 for non-members), `GET /crews/join/{token}` (signed-out stashes target URL in `session["post_login_redirect"]` and redirects to `/auth/google`; signed-in resolves invite → confirm page or invalid placeholder), `POST /crews/join/{token}` (idempotent, PRG to `/crews/{slug}?joined=1`). Google callback pops and honours `post_login_redirect`. `index`, `_attendance_response`, `event_detail`, and the profile route resolve `viewer_crews` once via `CrewService.get_viewer_crew_ids` and thread it into the visibility filters.
- `app/main.py`: crew list is inlined on `/settings` — there is no top-level `/crews` index route or nav link. `_settings_context` helper loads the viewer's crew list on both GET and POST-invalid so the section stays populated when the visibility form re-renders with an error.
- `app/templates/settings.html`: adds a "Crews" section below Visibility listing the viewer's crews (name → detail link) with a "Create a crew" CTA, empty state, and copy pointing back at the "Crews only" radio above.
- `app/templates/crews_new.html`: new. Single text input, error banner slot, submit.
- `app/templates/crews_detail.html`: new. Header, member list (avatar + name + Admin tag), invite-URL box with copy button, admin-only Rotate button, created / rotated / joined flashes, small-crew hint when member count < 4 (BRIEF small-N leak note).
- `app/templates/crews_hidden.html`: new. Same lock-icon placeholder as `profile_hidden.html`, no crew name, no member list — "This crew is invite-only. Ask a member for a link."
- `app/templates/crews_invite_confirm.html`: new. Crew name + Join button + Cancel to `/crews`.
- `app/templates/crews_invite_invalid.html`: new. "This invite link is no longer active" + Back link. No crew name leak.
- `app/templates/settings.html`: adds a third radio for `crews_only` between Public and Private with copy "Only runners in your crews can see your name and past races. Others still see counts."
- `static/css/main.css`: adds `.nav-crews`, `.crews-page`, `.crews-head`, `.crews-title`, `.crews-cta`, `.crew-list` / `.crew-row` / `.crew-row-name`, `.crews-empty` / `.crews-empty-sub`, `.crews-new-label` / `.crews-new-input`, `.crew-member-list` / `.crew-member-row` / `.crew-member-name`, `.crew-role-tag`, `.crew-small-hint`, `.crew-invite-box`, `.crew-invite-rotate`, `.crew-rotate-btn`, `.crew-invite-copied`.
- `static/js/crews.js`: new, ~30 lines. Clipboard copy for the invite URL with `document.execCommand('copy')` fallback for non-secure contexts. Wired into `crews_detail.html` only.

## [0.12.0]

### Changed — PR2 follow-ups: save flash, email hidden, preview mode, hidden-attendee stock fill

- `app/services/attendance_service.py`: `AttendanceSummary` gains `going_hidden_count` and `interested_hidden_count`. The grouping loop now increments the hidden counter when an attendee's identity is filtered out (previously the row was silently dropped from the identity list with no signal). Templates use this to render stock `ir` silhouettes in the slots that hidden attendees would otherwise have occupied, so a private user going to a race shows as a silhouette rather than only bumping the count. Signed-out viewers converge on the same path — every attendee is hidden → every slot fills with a silhouette.
- `app/schemas/race.py`: `EventListItem.going_hidden_count` / `interested_hidden_count` mirror the summary fields.
- `app/main.py`: `index`, `_attendance_response`, and `event_detail` populate the two hidden counters on their payloads.
- `app/templates/partials/avatar_strip.html`: new. Shared `avatar_strip(users, hidden_count, total, cap, size)` macro renders real avatars first, then stock silhouettes up to `cap`, then the `+N` overflow chip. Replaces the four near-duplicate anon/signed-in branches previously inlined in `race_tile.html` and `event.html`.
- `app/templates/partials/race_tile.html` and `app/templates/event.html`: both switched to the shared macro. The anon-branch `{% if not current_user %}` splits are gone — the same call handles anon (all hidden), signed-in-with-hidden (mixed), and signed-in-all-public (no stock) uniformly.
- `static/js/attendance.js`: `buildAvatarHtml(users, hiddenCount, total, cap)` mirrors the Jinja macro so mark/remove responses re-render the strip identically. All callers thread `going_hidden_count` / `interested_hidden_count` from the response payload.
- `app/main.py`: `GET /settings` gains a `saved: str | None` query param; `POST /settings` now redirects to `/settings?saved=1` on success. `settings.html` renders a green "Saved." flash banner when `saved=True`, giving the user visible confirmation of the write (previously PRG landed with no acknowledgement).
- `app/templates/settings.html`: adds the flash banner slot and swaps the "View my profile as others see it" link to `/profile/{id}?preview=1` with copy explaining that preview mode drops the self-view short-circuit.
- `app/main.py`: `GET /profile/{user_id}` accepts `preview=1`. When the viewer is the target and `preview=1` is set, the effective viewer id passed to `ProfileService` becomes a sentinel (`-1`) so the self short-circuit does not fire — the owner sees the profile exactly as a signed-in stranger would (private target → placeholder, public target → their own public profile without the self bypass).
- `app/templates/profile.html` and `app/templates/profile_hidden.html`: render a yellow "Preview" banner with a "Back to settings" link when `preview_mode=True`. The banner explains what preview mode shows so the user does not confuse it with a bug.
- `app/templates/profile.html`: `<div class="profile-email">` removed entirely — the address is never surfaced on the profile, even to self (email is auth-only, not a public identifier).
- Google avatars (`lh3.googleusercontent.com`): all `<img class="avatar">` tags in `race_tile.html`, `event.html`, `profile.html`, `avatar_strip.html`, and the JS-built markup gain `referrerpolicy="no-referrer"` to satisfy Firefox Opaque Response Blocking on Google-hosted images. Without it, Firefox blocked the response and every Google avatar fell back to the initial swatch.
- `static/css/main.css`: adds `.settings-flash` (green) and `.preview-banner` (yellow) styles.

### Added — Per-user visibility tri-state, settings page, gated profile route (privacy PR2)

- `migrations/009_users_visibility.sql`: adds `web.users.visibility VARCHAR(16) NOT NULL DEFAULT 'public'` with `CHECK visibility IN ('public','crews_only','private')`. Additive; existing rows land on `public` via the DEFAULT. `crews_only` is a valid column value from day one but the settings form does not offer it until PR3.
- `app/models/web.py`: `User.visibility` mapped column added.
- `app/services/attendance_service.py`: `get_attendance_summary` signature changed from `viewer_signed_in: bool` to `viewer_user_id: int | None`. Existing single-join query gains `User.visibility` in the select. New private helper `_is_identity_visible(user_id, visibility, viewer_user_id)` applies the rule: anon → hidden; self → always shown; `public` → shown to any signed-in viewer; `crews_only` / `private` → hidden in PR2 (PR3 swaps `crews_only` for a `shares_crew_with` check). `AttendanceSummary` gains `interested_users` alongside `going_users`, filtered by the same rule and capped at 4. Counts continue to include every attendee regardless of visibility.
- `app/services/profile_service.py`: `get_profile(target_user_id, viewer_user_id)` — signature changed from `viewer_is_self: bool`. Loads the target user + visibility at the top; collapses "missing user", "anonymous viewer", and "private / crews_only-blocked" into a single `ProfileView(is_visible=False)` return so the route can render one placeholder either way (no enumeration channel, no reason leak, no scraper-visible identity for anonymous visitors). `ProfileView` gains `is_visible: bool` and `target_user: User | None`. Interested shelf is no longer self-only — it now follows the same visibility rule as the rest of the profile.
- `app/services/settings_service.py`: new. `SettingsService.update_visibility(user_id, level)` validates `level ∈ {'public','private'}` and writes `web.users.visibility`. `crews_only` and any other value raise `ValueError`.
- `app/main.py`:
  - New `GET /settings` (renders `settings.html`) and `POST /settings` (form-encoded `visibility`, PRG redirect on success, re-render with error on `ValueError`).
  - `GET /profile` becomes a redirect shortcut to `/profile/{current_user.id}`.
  - New `GET /profile/{user_id}` — anon-accessible; on `is_visible=False` renders `profile_hidden.html`, else `profile.html` with `viewer_is_self`, `profile`, and `target_user`.
  - Three attendance call sites migrated to `viewer_user_id=…`.
  - `index`, `_attendance_response`, and `event_detail` now populate `interested_users` alongside `going_users` on the response payloads and template context.
- `app/schemas/race.py`: `EventListItem.interested_users: list = []` added, mirroring `going_users`.
- `app/templates/settings.html`: new. Header, one visibility section, two radios (Public/Private) with sub-copy, submit, and a "View my profile as others see it" cross-link to `/profile/{current_user.id}` with a caveat that self-view is always the full profile.
- `app/templates/profile_hidden.html`: new. Centered lock icon + "This runner keeps their profile private" + Back link. No name, avatar, id, stats — same wording for both hidden reasons.
- `app/templates/profile.html`: header + title now read from `target_user` (was `current_user`), so viewing another user's public profile shows their identity. Email row gated on `viewer_is_self`. Interested stat card gated on `profile.interested` (not `viewer_is_self`); Interested section is rendered whenever the shelf has entries or the viewer is self; vis-tag copy no longer branches on self.
- `app/templates/base.html`: nav gets a Settings link between the profile link and Log out.
- `app/templates/partials/race_tile.html`: base view and hover overlay gain a parallel interested strip gated on `race.interested_count > 0`. Signed-in path loops `race.interested_users[:3]`; anon path renders up to 3 stock silhouettes. Overflow chip and label mirror the going strip.
- `app/templates/event.html`: attendance strip gains an interested row (up to 4 avatars with `+N` overflow, or anon silhouettes).
- `static/js/attendance.js`: `updateTile` refactored to update or insert/remove the interested strip (tile base, hover, and event page variants) on mark/remove responses. Avatar helpers now take an explicit `cap` argument since going uses 3 (tile) or 4 (event) and interested mirrors those caps.
- `static/css/main.css`: adds `.nav-settings`, `.settings-page` / `.settings-section` / `.settings-radio` / `.settings-submit` / `.settings-preview` styles, `.tile-attendees--interested` / `.hover-attendees--interested` / `.event-attendance-avatars--interested` spacing, italic muted `.going-count--interested`, `.profile-avatar--photo` variant for real avatars on other users' profiles, and `.profile-hidden` placeholder layout.
- `docs/ARCHITECTURE.md`, `docs/FILE_TREE.md` updated for the new column, service, routes, and templates.

## [0.11.0]

### Changed — Signed-out UX: counts stay, identity hidden (privacy PR1)

- `app/services/attendance_service.py`: `get_attendance_summary` gains a `viewer_signed_in: bool = False` parameter. When false, the returned `AttendanceSummary.going_users` list is empty for every occurrence; `going_count` and `interested_count` are unaffected. SQL is unchanged (one query), so PR2's per-attendee visibility filter can extend the same result set without another pass. Safe default keeps identity hidden if a caller forgets to pass the flag.
- `app/main.py`: three call sites updated. `index` and `event_detail` pass `viewer_signed_in=current_user is not None`; `_attendance_response` (only reachable from authenticated POST/DELETE routes) passes `True`.
- `app/templates/partials/race_tile.html`: base and hover avatar strips now branch on `current_user`. Signed-in path unchanged. Anon path renders up to 3 stock silhouette glyphs (an inline SVG head-and-shoulders inside `.avatar.avatar--stock`) plus the existing overflow chip. Counts render as today.
- `app/templates/event.html`: same treatment on the event attendance strip — up to 4 `.avatar--lg.avatar--stock` silhouettes for anon.
- `static/css/main.css`: added `.avatar--stock` — neutral grey circle with the silhouette glyph in `--forest-mid`. Sizes automatically with `.avatar--lg`. Existing `.avatar`, `.avatar--initial`, `.avatar--overflow`, `.avatar--lg` untouched.
- No schema change, no auth change, no new dependencies. Interested identity is not surfaced today; PR2 will thread the tri-state and apply the same rule to interested.

### Removed — Terrain row from tile hover overlay

- `app/templates/partials/race_tile.html`: removed the Terrain hover-row from the event description panel. Terrain is still visible as the badge in the upper-left corner of each tile.

### Added — One-command local dev script

- `scripts/dev.sh`: starts the Cloud SQL Auth Proxy (skips if port 5432 is already bound) then runs `uvicorn app.main:app --reload` on `:8000`. Ctrl+C stops both. Proxy binary is downloaded on first run; gcloud auth is checked before starting.
- `docs/ARCHITECTURE.md`: updated "Local development" section to point at `dev.sh` as the primary entry point; `db_proxy.sh` noted as the standalone alternative.

### Fixed — Top-going events past the 60th date row now show up

- `app/services/race_service.py`: dropped the `result = result[:60]` truncation at the end of `list_races`. It ran on rows ordered by `race_date ASC`, so any event past the 60th nearest date (e.g. a 2027 race) was cut before attendance data was ever loaded. Symptom: tiles for far-future events with people going never appeared on the index.
- `app/main.py`: moved the 60-tile cap to after `races.sort(...)` so the ordering runs over the full candidate set and then trims. Image lookup and attendance summary now run against the full pre-sort set, which is fine for current volumes but worth watching if the base query ever grows into the thousands.
- `app/main.py`: sort key is now `going_count desc, interested_count desc, race_date asc` (previously `going_count desc, race_date asc`).

### Added — Sequential stock reassignment (one-time)

- `docs/stock_credits.md`: expanded to 53 entries. New: `trail_11..22` (12 new trail slots), `road_08..20` (13 new road slots plus a replacement `road_04` = Scott Szarapka aerial city view), `mixed_05..11` (7 new mixed slots).
- `app/imaging/inputs/stock/`: 22 new stock jpgs on disk to match. Removed the old `road_04` (rooftop Martin Reisch — political content). Renamed `mixed_05-...`, `mixed_08-...` (used dashes) to `_05_`, `_08_` so the manifest generator parses the slot correctly.
- `app/imaging/inputs/dedicated/`: added `road_berlin_half_marathon.jpg`.
- `app/imaging/stock_manifest.json`: regenerated with 53 entries.
- `docs/dedicated_credits.md`: added `berlin_half_marathon` (Eren Goldman).
- Published `tiles/v02/*` (passthrough) — 53 stock + 3 dedicated = 56 blobs uploaded. Deleted stale `tiles/v0[1-4]/stock/road_04_rooftop-...webp` and `originals/stock/road_04_rooftop-...jpg` from the bucket.
- One-time reassignment of stock tile slots in `web.event_images`: for each terrain, collected rows where `kind='stock'` and the event is not dedicated, joined `core.mv_denormalized_event_data` for earliest race date, sorted by (date asc null-last, event_id asc), and round-robin assigned manifest filenames in slot order. 75 rows updated (19 trail / 29 road / 27 mixed). The script was one-shot and deleted after apply — new events landing after this still get a random terrain-matched slot via `EventImageService.get_or_create_for_events`.

## [0.10.0]

### Changed — Dedicated tile flag now sourced from GCS, not DB

- `app/imaging/dedicated_index.py`: new module. `load_dedicated_slugs()` performs one anonymous `list_blobs` on `gs://indie-runners-web-tiles/originals/dedicated/` and returns the set of stems (event slugs). Bucket allows public list, so no ADC needed on the request path or in Cloud Run.
- `app/imaging/resolver.py`: signature changed to `resolve_tile_image(event_slug, event_image, dedicated_slugs)`. Dedicated branch is keyed on `event_slug in dedicated_slugs`; `web.event_images.kind` is no longer consulted for that decision. Stock branch still reads `event_image.stock_filename`.
- `app/main.py`: added a FastAPI `startup` event that calls `load_dedicated_slugs()` once and stashes the result on `app.state.dedicated_slugs`. Index route reads it from `request.app.state` and passes it into the resolver. To pick up a newly published dedicated photo the app must be restarted.
- `docs/IMAGING.md`: "Adding a dedicated photo" step-list shortened — the SQL UPDATE step is removed, a "restart the app" step is added. The `web.event_images.kind` column stays in the schema but is no longer written for dedicated events.
- `docs/ARCHITECTURE.md`: Static assets section notes the startup slug cache.

Migration to this behaviour: nothing. `web.event_images.kind` and `stock_filename` still drive stock persistence; only the "which events are dedicated" flag moved. Existing rows are unaffected.

### Added — Duotone palette control via CLI + per-terrain config

- `app/imaging/stylers.py`: `DuotoneStyler` now accepts `shadow`, `mid`, `highlight`, `contrast` via `__init__`. Class attrs renamed to `DEFAULT_SHADOW`/`DEFAULT_MID`/`DEFAULT_HIGHLIGHT`/`DEFAULT_CONTRAST` and become defaults when the args are omitted.
- `app/imaging/palette.py`: new module. `parse_hex('#RRGGBB' | 'RRGGBB')` returns an RGB triple. `terrain_from_filename(path)` reads the leading terrain from `{terrain}_...`, raises on missing/invalid. `load_duotone_config(path)` parses a JSON file mapping `trail|road|mixed` → per-component hex, validates keys and values. `resolve_duotone(terrain, config, global_shadow, global_mid, global_highlight)` returns a `DuotoneStyler` with per-component precedence: config[terrain] → globals → class default.
- `app/imaging/publish.py`: `publish_image` and `publish_all` now take a `styler_factory: Callable[[Path], ImageStyler]` instead of a single `ImageStyler`. For dedicated files, the on-disk `{terrain}_{event_slug}.jpg` has the terrain prefix stripped before upload — bucket paths remain `dedicated/{event_slug}.webp` so the resolver keeps working.
- `app/imaging/__main__.py`: added `--shadow`, `--mid`, `--highlight`, `--duotone-config` flags. All four apply only to `--style duotone`; a warning prints on stderr if they are passed with `grade` or `passthrough`. Missing terrain prefix on a dedicated file raises a clear error and exits non-zero.
- `docs/IMAGING.md`: CLI reference expanded with the new flags and a JSON config example. "Adding a dedicated photo" step 1 updated: the on-disk filename must now be `{terrain}_{event_slug}.jpg`; publish strips the prefix before upload.

### Added — Tile images wired into the race grid

- `migrations/008_event_images_stock_assignment.sql`: extends `web.event_images` with `kind VARCHAR(20) NOT NULL DEFAULT 'stock'`, `stock_filename VARCHAR(255)`, `terrain VARCHAR(20)`. Adds `ck_event_images_kind` (`kind IN ('dedicated','stock')`) and `ck_event_images_stock_has_filename` (`kind = 'dedicated' OR stock_filename IS NOT NULL`). Applied to local dev DB; table was empty so the CHECK adds cleanly.
- `app/models/web.py`: `EventImage` gains `kind`, `stock_filename`, `terrain` fields matching the migration.
- `app/config.py`: `Settings` gains `tile_version: str = "v01"`. Read at request time via `settings.tile_version`; flipping the served version is an env var + redeploy.
- `.env.example`: added `TILE_VERSION=v01` under a Tile images section.
- `app/services/event_image_service.py`: new `EventImageService.get_or_create_for_events(events)` — selects existing rows, picks a random terrain-matched stock slot for missing events (null / unknown terrain falls back to `mixed`), bulk `INSERT ... ON CONFLICT (event_id) DO NOTHING`, re-selects to pick up any concurrent inserts, returns a dict keyed by `event_id`. Manifest loaded once at module import.
- `app/imaging/resolver.py`: rewritten. New signature `resolve_tile_image(event_image) -> str`. Reads `settings.tile_version` at call time. Dedicated branch returns `.../v??/dedicated/{event_slug}.webp`; stock branch returns `.../v??/stock/{stock_filename}.webp`. No hash logic — assignment is persisted.
- `app/schemas/race.py`: `EventListItem` gains `tile_image_url: Optional[str] = None`.
- `app/main.py`: index route calls `EventImageService` between `list_races` and the attendance merge; populates `tile_image_url` per race.
- `app/templates/partials/race_tile.html`: added conditional `<img class="tile-photo">` tag with `loading="eager" fetchpriority="high"` on the first 4 tiles (above the fold) and `loading="lazy"` on the rest. `tile_index` is threaded in from `index.html` via a `{% set %}` in the parent loop (Jinja `{% include %}` does not propagate `loop`).
- `app/templates/index.html`: added `{% set tile_index = loop.index0 %}` before the tile include so `race_tile.html` can pick the eager-vs-lazy loading strategy.
- `static/css/main.css`: added `.tile-photo` rule (absolute, `object-fit: cover`, `z-index: 0`). Bumped `.tile::after` (dark gradient overlay) to `z-index: 1`, `.tile-base` to `z-index: 2`, `.tile-hover` to `z-index: 3`, `.tile-terrain-badge` to `z-index: 4`. Gradient class stays as a fallback background under the image.
- `scripts/deploy.sh`: added `--set-env-vars "TILE_VERSION=${TILE_VERSION:-v01}"` so the served version is controlled at deploy time via the shell env.
- `docs/IMAGING.md`: "Publishing a new version" section rewritten around the env var flip (Cloud Run `gcloud run services update` or `TILE_VERSION=vNN bash scripts/deploy.sh`). "Adding a dedicated photo" section updated: INSERT now sets `kind='dedicated'` (previous form failed the new CHECK) and uses `ON CONFLICT (event_id) DO UPDATE` because every event has a row after this task lands; the flag phrasing changed from "presence of the row" to "the row's `kind`".
- `docs/ARCHITECTURE.md`: added `TILE_VERSION` to the Required variables list.

### Added — Tile image pipeline (phase 4: publish and CLI)

- `app/imaging/publish.py`: `publish_image(input_path, styler, bucket)` reads original bytes, uploads to `gs://indie-runners-web-tiles/originals/{dedicated_or_stock}/{filename}.jpg` with `image/jpeg` content type, runs the styler, encodes WebP at quality 82, uploads to `tiles/v01/{kind}/{stem}.webp` with `image/webp`, and mirrors both to `app/imaging/outputs/`. `publish_all(styler)` walks `inputs/dedicated/` and `inputs/stock/` and prints one plain `publishing <filename>` line per file. Bucket name and `TILE_VERSION` are module constants.
- `app/imaging/__main__.py`: argparse CLI, `python -m app.imaging --style {duotone,grade}`, instantiates the chosen styler and calls `publish_all`.
- Ran `python -m app.imaging --style duotone` end to end against `gs://indie-runners-web-tiles`. 19 stock originals + 19 duotone WebP tiles uploaded and mirrored under `app/imaging/outputs/`. No dedicated files present yet; `dedicated/` walk is a no-op until originals are dropped in.

### Added — docs/IMAGING.md

- `docs/IMAGING.md`: ops reference for the offline tile image pipeline. Sections: overview, bucket layout, local layout, CLI reference, add-a-stock-photo, add-a-dedicated-photo, publish-a-new-version, side-by-side comparison workflow, bucket and ADC setup, deleting stale versions.
- `docs/ARCHITECTURE.md`: added a short "Static assets" section pointing at `docs/IMAGING.md`. Runtime service design stays here; ops procedure lives in the dedicated doc.

### Added — Compare multiple tile versions side by side

- `app/imaging/stylers.py`: added `PassthroughStyler` (resize to 600 px long edge, RGB, no color transform) as a baseline against `DuotoneStyler` and `ColorGradeStyler`.
- `app/imaging/__main__.py`: registered `passthrough` in the `--style` choices. Added `--tile-version` flag (default: `publish.TILE_VERSION`, currently `v01`) that overrides `publish.TILE_VERSION` at runtime so a single run publishes under any version prefix. Prints the target `tiles/<version>/` prefix at start.
- Published three parallel versions in `gs://indie-runners-web-tiles`:
  - `tiles/v01/stock/` — `DuotoneStyler` (site default; `resolver.py` still points here).
  - `tiles/v02/stock/` — `PassthroughStyler` (untouched color baseline).
  - `tiles/v03/stock/` — `ColorGradeStyler` (light wash).
- To flip the site to a version for comparison, change `TILE_VERSION` in `app/imaging/resolver.py`. Old prefixes stay in the bucket for free rollback.

### Changed — Dedicated bucket for web tiles

- New bucket `indie-runners-web-tiles` (europe-west1, Standard, Uniform access, `allUsers` = Storage Object Viewer). Separates web-owned public tile assets from the scraper's private bucket.
- Layout drops the `images/` prefix now that the bucket is dedicated: `originals/{dedicated,stock}/...` and `tiles/v01/{dedicated,stock}/...`.
- `app/imaging/publish.py`: `BUCKET_NAME = "indie-runners-web-tiles"`; original and tile GCS paths no longer prefixed with `images/`.
- `app/imaging/resolver.py`: `BASE_URL = "https://storage.googleapis.com/indie-runners-web-tiles/tiles"`.
- Public read verified: `curl -I` on a tile url returns `HTTP/2 200`, `content-type: image/webp`, `cache-control: public, max-age=3600`.
- Follow up: originals and duotone tiles under `images/` in `indie-runners-race-scraper` are now stranded and can be deleted manually.

### Added — Tile image pipeline (phase 3: stock manifest)

- `docs/stock_credits.md`: source-of-truth credits doc, one `## {terrain}_{NN} — Title` heading per stock image with a `Photo by <a>Name</a> on <a>Unsplash</a>` line. 19 entries (9 trail, 6 road, 4 mixed).
- `scripts/generate_stock_manifest.py`: parses the credits doc, cross-references with filenames in `app/imaging/inputs/stock/` by the `{terrain}_{NN}` prefix, writes `app/imaging/stock_manifest.json`. Aborts with a plain warning listing mismatched keys if any credit entry lacks a file or vice versa; does not overwrite the manifest on abort.
- `app/imaging/stock_manifest.json`: generated data file, checked in. 19 entries covering every current stock image.
- `migrations/007_event_images.sql`: applied to local Cloud SQL dev instance.

### Added — Tile image pipeline (phase 2: pure code)

- `app/imaging/stylers.py`: `ImageStyler` base, `DuotoneStyler` (grayscale + contrast 1.1 + colorize shadow (26,40,28), mid (45,68,48), highlight (240,243,234)), `ColorGradeStyler` (saturation 0.80, contrast 1.06, wash (45,68,48) at strength 0.10), shared `resize_long_edge` helper (600 px, no upscaling).
- `app/imaging/resolver.py`: `TILE_VERSION="v01"`, `BASE_URL` constant, `resolve_tile_image(event, dedicated_lookup, stock_manifest)`. Dedicated hits return `{BASE_URL}/v01/dedicated/{event_slug}.webp`. Stock uses `hashlib.md5(event_slug.encode()).hexdigest()` mod bucket size for stable indexing across process restarts. Terrain outside `trail/road/mixed` falls back to `mixed`. Pure, no IO.
- `app/imaging/stock_manifest.py`: `load_manifest(path=None)` reads and validates `app/imaging/stock_manifest.json`; `validate_entry` enforces required fields (`filename`, `terrain`, `slot`, `title`, `photographer_name`, `photographer_url`, `photo_url`) and terrain bucket. Parser lives in `scripts/generate_stock_manifest.py`, added in phase 3.

## [0.9.0]

### Added — Tile image pipeline (phase 1: skeleton and schema)

- `app/imaging/__init__.py`: new package for offline image pipeline (stylers, publish, resolver). Only `resolver.py` is intended for request-path import in a later task; nothing is wired in yet.
- `app/imaging/inputs/dedicated/.gitkeep`, `app/imaging/inputs/stock/.gitkeep`: placeholder drop directories for hand-picked and stock originals. Actual image files are gitignored.
- `.gitignore`: ignores `app/imaging/inputs/**/*.{jpg,jpeg,png,webp}` and `app/imaging/outputs/` (top-level `outputs/` rule does not cover the nested path).
- `requirements.txt`: added `google-cloud-storage>=2.16.0` for GCS uploads in the publish step.
- `migrations/007_event_images.sql`: creates `web.event_images` (`id`, `event_id`, `event_slug`, `source`, `attribution`, `created_at`, `updated_at`) with `UNIQUE (event_id)` and `idx_event_images_event_slug`. Soft reference to `core.events`, same pattern as `web.attendance`. Presence of a row is the dedicated-tile flag; no boolean.
- `app/models/web.py`: added `EventImage` model matching the migration (`event_id`, `event_slug`, `source`, `attribution`, timestamps; `uq_event_images_event_id`; `idx_event_images_event_slug`).

## [0.8.0]

### Added — User profile page

- `migrations/005_attendance_race_date.sql`: added `race_date DATE` and `event_display_name VARCHAR(255)` snapshot columns to `web.attendance`; backfilled `race_date` from `MAX(occurrence_start_date)` in `core.mv_denormalized_event_data` grouped by `event_id`; backfilled `event_display_name` from MV
- `migrations/006_attendance_occurrence_id.sql`: added `occurrence_id INTEGER` to `web.attendance`; backfilled from `core.event_occurrences` joining on `event_id` and `start_date = race_date`; dropped `uq_attendance_user_event`; added `uq_attendance_user_occurrence (user_id, occurrence_id)` and `idx_attendance_occurrence_id` — attendance is now edition-level, one row per user per occurrence
- `app/models/web.py`: added `occurrence_id`, `race_date`, `event_display_name` to `Attendance`; updated unique constraint and indexes to match migration 006
- `app/schemas/race.py`: added `occurrence_id` to `EventListItem`
- `app/services/race_service.py`: populates `occurrence_id` from MV per event group
- `app/services/attendance_service.py`: re-keyed all methods to `occurrence_id`; `mark_attendance` now takes `occurrence_id` and snapshots `race_date` from `core.event_occurrences` and `event_display_name` from `core.events` on insert; `clear_attendance` skips delete if `race_date < today` to preserve past history
- `app/services/profile_service.py`: new `ProfileService` — `get_profile(target_user_id, viewer_is_self)` builds `ProfileView` with `going_upcoming`, `going_past`, `interested` shelves; single query joining `web.attendance`, `core.events`, `core.event_occurrences`; interested shelf only populated when `viewer_is_self=True`
- `app/main.py`: attendance routes changed from `/events/{event_id}/attendance` to `/events/{event_id}/{occurrence_id}/attendance`; index and event detail routes re-keyed to `occurrence_id`; added `GET /profile` route; `occurrence_id` passed to event detail template
- `app/templates/base.html`: nav username replaced with link to `/profile`
- `app/templates/profile.html`: new template — profile header with avatar initial, stats strip (Going / Been there / Interested), Going rows (name link, location, terrain badge, date), Past chips (name + muted location), Interested mini-cards (self-only, `{% if viewer_is_self %}`)
- `app/templates/partials/race_tile.html`: added `data-occurrence-id` to tile div and all attendance buttons
- `app/templates/event.html`: added `data-occurrence-id` to attendance block div and all attendance buttons
- `static/js/attendance.js`: reads `occurrenceId` from button dataset; fetch URL now `/events/{eventId}/{occurrenceId}/attendance`; rebuilt button HTML preserves `data-occurrence-id`
- `static/css/main.css`: added profile page styles — `.profile-page`, `.profile-head`, `.profile-avatar`, `.profile-stats`, `.profile-stat`, `.profile-section`, `.profile-race-row`, `.profile-terrain-badge`, `.profile-race-date`, `.profile-past-grid`, `.profile-past-chip`, `.profile-card-grid`, `.profile-mini-card`, `.vis-tag`, `.nav-profile`

## [0.7.0]

### Changed — Google OAuth replaces Strava login

- `migrations/003_google_auth.sql`: added `email`, `display_name`, `avatar_url` columns to `web.users`; backfilled `display_name` from `firstname || lastname`; backfilled `avatar_url` from `profile_photo_url`; dropped NOT NULL on `strava_athlete_id` (Google users have none); created `web.auth_identities` table with `(provider, provider_user_id)` and `(user_id, provider)` unique constraints
- `app/models/web.py`: added `email`, `display_name`, `avatar_url` to `User`; made Strava columns nullable (kept until migration 004); added `AuthIdentity` model
- `app/config.py`: removed `STRAVA_CLIENT_ID/SECRET/REDIRECT_URI`; added `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `app/services/auth_service.py`: replaced `StravaAuthService` with `GoogleAuthService` (`build_authorize_url`, `exchange_code_for_token`, `get_userinfo`)
- `app/services/user_service.py`: replaced `get_or_create_user_from_strava` with `get_or_create_user_from_google`; gates on `email_verified`; upserts both `web.users` and `web.auth_identities`
- `app/services/attendance_service.py`: `AttendanceUserInfo` fields `firstname`/`profile_photo_url` → `display_name`/`avatar_url`; query updated
- `app/main.py`: removed `GET /auth/strava` and `GET /auth/strava/callback`; added `GET /auth/google` and `GET /auth/google/callback`; all `going_users` dicts updated to new field names; `/me` returns `email`, `display_name`, `avatar_url`
- `app/templates/base.html`: Strava button replaced with Google sign-in button; `current_user.firstname` → `current_user.display_name`
- `app/templates/index.html`: hero eyebrow "Strava friends" → "Your running community"
- `app/templates/event.html`: avatar fields updated; "Sign in" link → `/auth/google`
- `app/templates/partials/race_tile.html`: avatar fields updated; "Sign in" link → `/auth/google`
- `static/js/attendance.js`: `firstname`/`profile_photo_url` → `display_name`/`avatar_url`; 401 redirects → `/auth/google`
- `static/css/main.css`: replaced `.strava-btn` with `.google-btn` styled to match site palette (forest green background, off-white text); replaced `.strava-icon` with `.google-icon`
- `scripts/deploy.sh`: replaced Strava secret refs with Google secret refs; `STRAVA_REDIRECT_URI` env var → `GOOGLE_REDIRECT_URI`
- `.env.example`: removed Strava vars; added Google vars with comments; added `SECRET_KEY` rotation note
- `docs/ARCHITECTURE.md`: updated auth section, tables, service classes, env vars, secrets

## [0.6.0]

### Added — Tile title link style on reveal

- `static/css/main.css`: added `--link-on-dark: #7db87a` CSS variable in `:root` for links on dark surfaces (distinct from `--forest-mid` which is for light backgrounds)
- `static/css/main.css`: `.tile:hover .tile-hover .tile-name-link` and `.tile--revealed .tile-hover .tile-name-link` — title turns green (`--link-on-dark`) and underlined when the tile is revealed
- `static/css/main.css`: `.tile--revealed` rules mirror the `:hover` overlay state (darkened `::after`, `tile-base` opacity 0, `tile-hover` visible with `pointer-events: auto`) for mobile tap support
- `static/css/main.css`: `.tile-hover` top padding increased from `1.4rem` to `2.8rem` so revealed content clears the absolutely-positioned terrain badge
- `static/js/attendance.js`: added mobile tap-to-reveal handler (guard: `window.matchMedia('(hover: none)')`); first tap adds `tile--revealed` and prevents navigation; second tap on the title navigates; tap outside any tile collapses all revealed tiles; attendance buttons bypass reveal logic via `[data-action]` guard

### Changed — Attendance keyed by event_id instead of race_id

- `migrations/002_attendance_event_id.sql`: migrated `web.attendance` — replaced `race_id` column with `event_id`; backfilled from `core.mv_denormalized_event_data`; new unique constraint `uq_attendance_user_event (user_id, event_id)`; new index `idx_attendance_event_id`
- `app/models/web.py`: `Attendance.race_id` → `Attendance.event_id`; updated constraint and index names
- `app/services/attendance_service.py`: all methods renamed from `race_id` to `event_id`; routes and service signature now operate on event-level attendance
- `app/main.py`: attendance routes renamed `/races/{race_id}/attendance` → `/events/{event_id}/attendance`; index route builds `event_ids` list instead of `race_ids`
- `static/js/attendance.js`: all `data-race-id` reads → `data-event-id`; fetch URLs updated to `/events/{id}/attendance`
- `app/templates/partials/race_tile.html`: all `data-race-id` attributes → `data-event-id`

### Added — Search filter

- `app/services/race_service.py`: added `search: Optional[str] = None` field to `RaceFilters`; added `or_` ILIKE condition on `race_name`, `race_location`, `terrain_type` in `list_races()`
- `app/main.py`: added `search` query param to `_parse_filters()` and `GET /` route; included in `has_active_filters` check
- `app/templates/index.html`: added Search text input as first filter group; value persists via `filters.search`

## [0.5.0]

### Added — Deployment

- `Dockerfile`: `python:3.11-slim` base image; installs `requirements.txt`; copies `app/`, `static/`, `templates/`; runs `uvicorn` on `$PORT`
- `.dockerignore`: excludes `.git`, `.venv`, `__pycache__`, `.env`, `docs/`, `scripts/`, `migrations/`
- `scripts/deploy.sh`: `gcloud builds submit` + `gcloud run deploy` targeting `europe-west1`, 512Mi, min 0 / max 5 instances, secrets injected from Secret Manager, `indie-runners-web` service account
- Cloud Run service `indie-runners-web` deployed to `europe-west1`; Cloud SQL connected via Unix socket sidecar to `europe-west10` instance
- Secrets created in Google Secret Manager: `indie-runners-web-strava-client-id`, `indie-runners-web-strava-client-secret`, `indie-runners-web-secret-key`, `indie-runners-web-database-url`
- Service account `indie-runners-web` created with roles: `Cloud SQL Client`, `Secret Manager Secret Accessor`, `Cloud Run Invoker`
- Custom domain `beta.indierunners.co` mapped via Cloud Run domain mappings

## [0.4.0]

### Added — Attendance

- `app/services/attendance_service.py`: `AttendanceService` with `mark_attendance`, `clear_attendance`, `get_attendance_for_user`, `get_attendance_summary`; one JOIN query for summary, Python grouping for counts/avatars
- `app/schemas/race.py`: added `interested_count`, `going_users`, `user_status` fields to `EventListItem`
- `app/main.py`: `POST /races/{race_id}/attendance` and `DELETE /races/{race_id}/attendance` routes; merged attendance summary + user attendance into `GET /` (3 queries max per pageload)
- `app/templates/partials/race_tile.html`: real going count and avatars (photo or initial fallback); `tile--mine` class; conditional hover CTA (sign in / going+interested buttons / change+remove links)
- `static/js/attendance.js`: vanilla JS fetch for mark/remove; DOM update without reload; 401 redirect; 2s error flash; ~90 lines
- `static/css/main.css`: avatar styles (26px base, 30px hover, 4-color palette, initial fallback); `tile--mine` outline; attendance button variants
- `requirements.txt`: added `python-multipart` (required for FastAPI `Form`)
- `app/main.py`: race list sorted by `going_count desc, race_date asc` after attendance merge (moved from `race_service.py` so counts are populated before sorting)
- `app/main.py`: post-login callback now redirects to `/` instead of `/me`

## [0.3.0]

### Added — Race grid page

- `app/models/core.py`: corrected column names to match view (`race_distance`, `race_status`; dropped unused bools)
- `app/schemas/race.py`: `EventListItem` pydantic schema — one item per event with `distances: list[float]`
- `app/services/race_service.py`: `RaceService` with `list_races(filters)`, `country_list()`, and `assign_gradient()`; groups view rows by `event_id` so one tile = one event
- `app/main.py`: static files mount, filter parser `_parse_filters()`, `GET /` route with `has_active_filters` flag
- `app/templates/base.html`: common layout with nav, Google Fonts, conditional Strava login / user+logout
- `app/templates/index.html`: hero, filter form (GET, Apply button, Clear filters link), race grid, suggest-a-race banner; JS strips empty inputs before submit to keep URL clean
- `app/templates/partials/race_tile.html`: tile with gradient class, terrain badge, distance pills on hover, `going_count` placeholder
- `static/css/main.css`: full styles from mockup plus nav logged-in state, Apply button, Clear filters link

## [0.2.0]

### Added — Strava OAuth

- `app/services/auth_service.py`: `StravaAuthService` with `build_authorize_url()` and async `exchange_code_for_token()` using httpx
- `app/services/user_service.py`: `UserService` with `get_or_create_user_from_strava()` — upserts `web.users` by `strava_athlete_id`
- `app/main.py`: `SessionMiddleware` (signed cookies, httponly, samesite=lax, secure in prod)
- `app/main.py`: `get_current_user` and `get_required_user` FastAPI dependencies
- Routes: `GET /auth/strava`, `GET /auth/strava/callback`, `GET /me`, `GET /auth/logout`
- `app/config.py`: `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REDIRECT_URI` settings
- `requirements.txt`: added `httpx` and `itsdangerous`

## [0.1.0]

### Added — Database connection

- Initial project scaffold: FastAPI app, SQLAlchemy 2.x setup, Jinja2 templates directory
- `app/config.py`: pydantic-settings `Settings` class reading `DATABASE_URL`, `SECRET_KEY`, `DEBUG`, `PORT` from environment
- `app/db.py`: SQLAlchemy engine, `SessionLocal`, `Base` with `MetaData(schema="web")`, `get_db` dependency
- `app/main.py`: FastAPI app with `GET /debug/health` returning status, race count, and user count
- `app/models/web.py`: `User` and `Attendance` SQLAlchemy models in the `web` schema
- `app/models/core.py`: read-only `Race` model mapping `core.mv_denormalized_event_data`
- `migrations/001_create_web_schema.sql`: SQL migration creating `web.users` and `web.attendance`
- `app/templates/`: empty Jinja2 templates directory
- `.env.example`: documents all required environment variables
- `docs/`: architecture, file tree, and changelog documentation
