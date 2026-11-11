# Ideas

> Paulo's inbox, not a roadmap: an entry here is not planned or promised.
> Written by the roles for each other, not for a reader; public since 2026-11-09.

Paulo's inbox. Anything worth not losing: a direction, a doubt, a
half-formed suggestion from another session, a thing that felt wrong
while looking at something else.

**Tracked in git, deliberately.** The audit reports live under
`exports/`, which is gitignored — right for them, since re-running a
sweep regenerates a finding. Ideas carried across sessions exist nowhere
else.

## How to add one

Append. Do not organise or rank — that is the PM's pass, and the friction
of pre-judging is what makes an inbox go unused.

```markdown
## <short title>
<date> · <status: raw | discussed | ticketed W-### | dropped>

<Whatever you have. If it is a hunch, say it is a hunch.>
```

Leave entries in place once ticketed or dropped, with the status updated.
A dropped idea that keeps recurring is a signal.

## Who reads it

The **PM**, on every triage pass. Ticketed (with the id), dropped **with
a reason**, or left raw with a note on what would settle it.

An idea that changes **direction** rather than adding work is not a
ticket — it is a `docs/PLAN.md` rewrite, and the PM should say so.

## Keep finished events on the front end for three days
2026-08-28 · **ticketed W-012** (p2, `tickets/W-012-retain-finished-events.md`)
· **stopped at Step 1, 2026-10-21.** The view drops a non-TBC race at
midnight after its date, so `D+1`/`D+2` needs a scraper-side view change.
See the ticket.

*PM 2026-08-28 — ticketed as written, and it is the first entry in this
file that **changed the arc**: `docs/PLAN.md` said IDEAS was empty and
excluded features, and both are now amended rather than rewritten — the
hardening arc still holds, this lands on top of it. Two things the ticket
took from you and one it added. Taken: the **dates are the spec** (Aug 1
finish -> visible through Aug 3, gone Aug 4, i.e. `+2` not `+3`) and the
premise query is **step 1 with a stop condition** — if the view drops
past rows the ticket routes to the scraper and halts rather than widening
a filter against data that is not there. Added: the per-race filter is
already corrupting **partly-past multi-day events**, whose early races
vanish from the tile's distances and formats before the event is over.
That makes this a grain fix, not a window fix, and is why it is `M`.*

Paulo, and he flags this as **high priority**.

An event should stay visible after it is over, not disappear the moment
it finishes. In his words: if an event's last race started **August 1st**,
it should still be there through **August 3rd**, and by **August 4th** it
should no longer appear. Recording the example rather than the phrase
"three days after" on purpose — the two do not quite agree, and the dates
are the tighter statement, so whoever specs this inherits the boundary
and not the ambiguity.

Note the key is the event's **last** race, not its first. An event whose
races run Aug 1–3 is not "done" on Aug 1.

**What happens today.** `RaceService.list_races`
(`app/services/race_service.py:157` and the `WHERE` at :173-189) keeps
rows with `race_date >= yesterday` — a one-day window, applied
**per race**, before the rows are grouped into events. So a finished
event drops off roughly a day after its last race. The grouping loop
already computes `race_date_end` (the event's latest race date), but only
after the filter has run, so it is not available to it.

**What would settle it: does the upstream view still carry past-dated
rows?** Everything the index reads comes through
`core.v_denormalized_event_data_upcoming`, which is scraper-owned and
filters to the current occurrence. If that view drops a race once it is
past, no filter change in this repo can retain the event and half of this
idea routes to `indie-runners-scraper` — this repo cannot fix `core.*`
(`docs/roles/README.md`). Hunch that it does retain them: the app's own
`>= yesterday` filter would have nothing to do otherwise. That is an
inference from the code, not a measurement — one query against the view
settles it, and the connection budget says that query belongs to whoever
picks this up, not to filing the idea.


## move official website
2026-08-28 · **ticketed W-013** (p4, `tickets/W-013-move-official-website-link.md`)

*PM 2026-08-28 — ticketed as asked, scoped to the hero link only. One
thing worth knowing that the request could not: the link is styled
`color: #fff` with a white underline because it sits on the photo, so
moving the markup alone renders white text on the card — it would look
correct in the diff and be invisible on the page. The ticket makes the
restyle and the browser check acceptance criteria. p4 rather than high:
nothing is blocked by it, so it rides the next batch.*

the event page shows the link to the official website within the hero image of the race. I would like this link to be moved out of the hero and be placed right after the events summary and before the buttons. 



## A stats page: recently-updated list, a refresh rollup, and a coverage map
2026-09-01 · **ticketed W-025 (list + rollup + headline), W-026 (map)**, 2026-10-21 · **source: `indie-runners-scraper` PM triage,
2026-09-01** — raised by Paulo in a scraper-side session, measured there,
and routed here because it is frontend work on this repo's surface.

*PM 2026-10-21, settled the same day: Paulo chose two labelled numbers, `core.events` for the headline and the serving view for the map. See W-025.* Before that: The
blocker was T-051, and it landed on 09-09. **What is left is the
denominator, and that is Paulo's call.** Item 3 can be built today, and
items 1–2 can once he picks. One fact for that choice: the view's
"upcoming" count fell from 360 to 301 in seven weeks (AUDIT_20261021 F6)
as the season ended. A headline built on the view would shrink every
autumn, which argues for a denominator that does not.

**All evidence is quoted inline.** The scraper repo's `exports/` is
gitignored and its `docs/` is not readable from this clone, so a path
would be unreadable here by construction.

**Three related asks, one page.** Paulo's framing for the first: *"sort of
a live blog of what is happening, so that users know that there is
movement in the back."*

### 1. A "recently updated" list

The events whose data was most recently refreshed, so a visitor sees the
catalogue is being worked on rather than sitting still.

**The cadence is the constraint, and it is the reason this is an idea
rather than an obvious build.** Measured against production 2026-09-01:

| Question | Answer |
|---|---|
| distinct events with a successful run, last 24h | **8** |
| last 7 days | 96 |
| last 30 days | 304 |
| days in the last 30 with **zero** successful runs | **11** |
| longest gap between consecutive successful runs (60d) | **9 days 18h** |
| median gap between successful runs | 19 minutes |

The distribution is bursty — long silences punctuated by bursts — so a
literal timestamped ticker would read "nothing happened" about one day in
three, and once would have sat unchanged for nearly ten days. **That
communicates the opposite of the thing it is for.**

What survives that: a **list of the last N, with no age filter**, so it is
never empty. What does not: relative timestamps as the primary framing —
"2 minutes ago" is the good day, "9 days ago" is the ordinary one.

**Do not expose the run counters.** The underlying table is operational:
`questions_answered` vs `questions_attempted`, `error_message`,
`trigger_type`. One real row reads `168/244`; publishing that announces a
31% miss rate per event. **Event name and a timestamp are the whole of
what belongs on a public page.**

**An honesty limit worth inheriting deliberately.** A `success` row does
not mean the site was fully readable — the scraper repo has an open
question on how much of a site must be reachable for a run to count. That
is the argument for the words **"last checked"** over "last verified".

### 2. The rollup — "304 events refreshed in the last 30 days"

The aggregate companion, and the half that actually conveys scale. It is
immune to the gap distribution that makes a per-day figure embarrassing:
11 of the last 30 days had zero successful runs, so "today: 0" is a third
of all days, while the 30-day number was never once misleading over the
same period. A window wider than the longest observed silence (9d 18h)
cannot show dead air.

### 3. A coverage map — events per country

**Backend cost is near zero, and the obvious column is a trap.**
`core.events.country_code` is **100% NULL — 489 of 489 rows** — so a
reader who checks it concludes the data does not exist.

The materialized view does not read that column. It sources country from
`race_scraper.website_targets`, so **the MV already carries it**:

- `event_country_alpha2` — ISO alpha-2, the form a map library wants
- `event_country_code` — lowercased country name
- fill rate **17 NULL of 1,842 rows (~0.9%)**
- `idx_mv_denorm_country_code` **already exists**

So it is a `GROUP BY` on an indexed column of the view this app already
serves from. No migration, either side.

Distribution, 2026-09-01 — 47 distinct countries, targets basis:

```
DE 127 · PL 95 · AT 61 · DK 29 · GB 27 · FR 27 · ES 25
NL 20 · CZ 12 · IT 7 · GR 5 · PT 4 · CH 4 · HR 3 · SE 3
```

### The one open decision, and it governs items 2 and 3 identically

**The denominator is a product question and the scraper PM deliberately
did not settle it.** Four numbers, all honest, all different:

| Number | Sentence it supports |
|---|---|
| 497 targets | "we monitor" |
| 489 events (`core.events`) | "we have discovered" |
| **361** (distinct events in the MV) | "we have race-level data to show" |
| 360 (`v_..._upcoming`) | "we have data for a *future* race" |

A map built off the MV shows 361; off `website_targets`, 497. **Coverage
claims are precisely where an unlabelled denominator misleads**, so
whichever is chosen should be named on the page.

One practical constraint: if the map is clickable, a country counted from
`website_targets` can contain zero MV rows and **the click dead-ends** —
which argues for targets in the headline count and the MV behind any link.

### What the scraper side is doing, so this is not blocked on guessing

**The per-event freshness timestamp is `T-051` on the scraper board**, and
it is the only part of all this that could not be built here. The reason:
the correct value is
`GREATEST(max(pipeline_runs.ended_at) WHERE status='success',
core.events.last_scraped_at)`, and `pipeline.*` is not reachable from this
app — `app/models/core.py:11` binds `MetaData(schema="core")` and there is
no reference to `pipeline.*` anywhere in `app/`.

Neither source alone is sufficient: 485 of 489 events have a successful
run row, but `last_scraped_at` runs **ahead** of the last run for **189 of
them, by up to 92 days** (`berlin_marathon`), because standalone
`tier_answers` invocations and adhoc rerun/backfill scripts open no run
row.

**A warning that matters on this side too: do not reach for
`events.updated_at` or `races.updated_at` as a freshness signal.** The
scraper's `core_tables` upserts are corpus-wide rather than
target-scoped — no `WHERE` on the event — so on 2026-09-01 **8 successful
runs touched all 488 event rows and 2,225 race rows**. Those columns mean
"the corpus was rebuilt", not "this event was checked".

T-051 will add the freshness value to the serving view as an **additive**
column, since this app marks the view READ ONLY and deploys separately.
**Items 1 and 2 want that column for their ordering; item 3 needs nothing
and can be built today.**

### DELIVERED 2026-09-09 — the column is live and is called `event_last_checked_at`

**Scraper side, 0.62.0, migrations 068 + 069. Nothing is owed back to
that repo; this is the notification the ticket required.**

```
core.v_denormalized_event_data_upcoming.event_last_checked_at
    timestamp with time zone
```

Appended **last**, so every existing column keeps its position — this app
binds the view READ ONLY and deploys separately, and that was the
constraint the addition was shaped around.

**Bind it as `DateTime`, not `Text`.** An earlier version of this note
said the column was `text` "to match `event_last_scraped_at` beside it,
cast on read if you need a timestamp" — that shipped in migration 068 and
was corrected in 069 before the release. It is a **derived** column, and
the scraper's MV types derived columns (`race_date` is `date`,
`start_time` is `time`) while leaving only passthrough ones `text`. No
cast on read, and no string parsing: it arrives as a datetime. The
neighbouring `event_last_scraped_at` **is** still `text` — the two look
alike and are not.

**What it means:** `GREATEST(max(pipeline_runs.ended_at WHERE
status='success'), core.events.last_scraped_at)`, per event. It is
**never NULL** on any current row.

**Numbers refreshed against production 2026-09-09** — the ones in the
section above are from 09-01 and have drifted: **182 of 491** events (not
189 of 489) have `last_scraped_at` ahead of their last successful run,
worst still `berlin_marathon` at **93 days**. The new column differs from
`event_last_scraped_at` on **205 events**, so ordering by it is not the
same as ordering by what you have today.

**Two limits to render honestly, both measured:**

- **It is "last checked", not "last verified".** A `success` row does not
  mean the site was fully readable, and **62% of successful runs are
  gate-shut** — tier 0 ran, found no upcoming-edition date, and never
  asked the detail questions. That is a real check with a real negative
  result, but it is why **this must not become a per-field badge**. Event
  level only.
- **48 served events carry answers that can never refresh** (T-092
  orphans; worst `sofia_marathon`, 61 of 67 rows). No event is *entirely*
  orphaned, so the badge never goes stale and the claim stays true — but
  on those events it reads "checked recently" over data frozen in July.

**Still do not use `events.updated_at` or `races.updated_at`** — the
warning above stands. One correction to it: `core.event_answers.updated_at`
became genuinely per-target on the scraper side in 0.59.0, so the
"corpus was rebuilt" argument no longer applies to *that* column. It is
still the wrong one here — it says when an answer set was rebuilt, not
when the event was last checked.

## Tile price should be a range, not a single number
2026-09-03 · **ticketed W-016** (p2, `tickets/W-016-tile-price-range.md`)

*PM 2026-09-04 — ticketed, and scoped to exactly what Paulo asked for
once the premise was corrected: a range across the event's races, that
is it. Worth recording that the correction changed **why** the tile is
wrong, not **whether** — it renders the earliest-dated race's price
under a `+` that asserts a floor, so it can state the dearest price as a
minimum. That is wrong data on an anonymous page, so the ticket is p2
rather than the p4 a display tweak would earn. Two calls taken in the
ticket rather than passed on: free races render `Free – €123`, keeping
the vocabulary the template already uses; mixed currency falls back to a
single value with no `+`, never a converted range, with the frequency
measured by whoever picks it up. The trap named in the spec is that `0`
and `NULL` must stay distinct — an unpriced race is unknown, not free,
and must never become the floor of a range.*

Paulo. If an event's cheapest race is 20 and its dearest is 80, the tile
should read `20 - 80€` rather than a single figure.

**One correction to the premise, and it makes the idea stronger.** The
tile is not showing the lowest price. `list_races` takes
`registration_price` and `price_currency` in the **first-see** branch of
the grouping loop (`app/services/race_service.py:242-243`), so the tile
shows the price of whichever race sorted earliest by date — which is not
the cheapest, and on an event whose earliest race is the 100km ultra it
is the dearest. The template
(`app/templates/partials/race_tile.html:4`) then renders it as
`{currency} {price}+`, and that trailing `+` currently asserts something
untrue: it reads as "from 20", i.e. a floor, when the number is not a
floor at all. So this is not only a nicer display — the tile is currently
capable of stating a minimum that is really a maximum.

This is the same class of bug `ARCHITECTURE.md` already documents twice
under the read model ("reading such a field off `rows[0]` is a bug, and
has been one twice" — the hero-image terrain, and the format filter).
Price is a race-level field being read as if it were event-level. The
grouping loop already does the right thing for `distances`, `formats` and
`cutoffs` by collecting across every row; price is the one that was left
on first-see.

**Two things a spec has to decide.**

- **Mixed currencies within an event.** `price_currency` is race-level
  too, and is taken on first-see alongside the price. A range across two
  currencies is meaningless, so the ticket needs a rule — hunch: if an
  event's races disagree on currency, fall back to a single value or
  show nothing rather than inventing a converted range. Unknown how often
  this actually happens; a `GROUP BY event_id` over distinct
  `price_currency` settles it in one query.
- **The degenerate cases.** All races the same price (show `20€`, not
  `20 - 20€`), only some races priced, and free races — the template
  already has a `Free` branch for `price == 0` and a `—` branch for
  missing, and a min/max both have to keep working with those. Whether
  an unpriced race means "free" or "unknown" is a source-data question,
  and the existing code treats `0` and `NULL` as different, so preserve
  that.

Cheap either way: the fix is collecting prices per row the way `cutoffs`
already are, then a min/max at render. No DB change, no `core.*` change —
this one is entirely this repo's.

## PM sweep of `exports/ideas/` — a second inbox nobody was reading
2026-09-08 · **triaged** · W-017, W-018 cut; one dropped, one left raw

Paulo pointed at `exports/ideas/apex_domain_followups.md`. It turned out
to be one of **four** files in a directory that predates this inbox and
is in no role's brief. `exports/` is gitignored, so nothing in there is
tracked, readable from a worktree, or visible to a review. **The fates
are recorded here because a status line edited in an untracked file is
not a record.** Nothing further should be filed there; this is the inbox.

The directory's defect in one line: `privacy_tiers_and_crews.md` (July,
16KB of design) still says **"Status: not built"** and is *fully
shipped* — verified in code, all three visibility tiers, crews, invites
and the settings page. A second inbox drifts because no pass ever reads
it.

- **`apex_domain_followups.md`** — the live one, and the reason the
  sweep was worth it. Six deferred items from the 2026-07-27 apex
  rollout, every one gated on "~7 days of stability". Six weeks passed.
  **Item 1 → W-017** (302 → 301; the gate expired unnoticed rather than
  failed, and W-006/W-010 make the SEO half concrete). **Items 2-4 →
  W-018** (decommission beta; operator work, no branch). **Item 5**
  (move the redirect to a CDN/DNS layer) **dropped** — its own text says
  "never, unless we grow tired of the middleware hop", and it splits
  redirect rules across code and an invisible CDN config for one hop on
  a low-traffic site. **Item 6** (watch for stray non-apex callback
  hits) **dropped as a ticket** — it is a habit, not work, and W-018
  step 1 makes it moot for beta.
- **`privacy_tiers_and_crews.md`** — **shipped**, no action, file
  deleted 2026-09-08. Its status line said "not built". Its deferred
  tail is carried below rather than lost with it.
- **`pre_assign_stock_sweep.md`** — **dropped with reason.** Lazy-on-read
  assignment is self-healing and race-safe, so a sweep buys nothing
  today. Revive if any of its own three conditions arrive: a CDN in
  front of the index, wanting to review assignments before they go live,
  or a bulk reassign after a manifest change.
- **`credits_page.md`** — **left raw**, per the third fate. ~1h of work
  (route, template, footer link, CSS) and the manifest already carries
  everything. **What would settle it:** its two defer reasons are still
  true — OAuth is in Testing mode behind a 100-user cap, so no wide
  audience sees the photos, and the tile visual is still moving. Ticket
  it when either changes, or sooner if Paulo just wants it.


## Privacy/crews: four things deferred by design, carried from a deleted file
2026-09-08 · raw · **rescued from `exports/ideas/privacy_tiers_and_crews.md`
before deletion** — the design shipped, these did not

The visibility tri-state, crews, invites and the settings page are all
live. These are the pieces its author deliberately *did not* build, kept
because each names a user and a trigger, and that reasoning exists
nowhere else now. **None is a ticket today** — every one is gated on a
complaint that has not arrived. Recorded so that when one does, the
answer is not re-derived from scratch.

- **A second lever for `interested`.** Show commitments (going) while
  hiding musings (interested). One lever ships now; a second
  `visibility` column is additive and cheap. *Trigger:* someone asks for
  the "going public, interested private" persona — **Ivy is the
  hint**.
- **Per-event override on interested** — opting one race in or out
  against your global level. Gus's original phrasing. *Trigger:* the
  tri-state alone proves insufficient now that crews have landed.
- **Blocking modal at signup** — **rejected**, not deferred. Friction at
  the highest-engagement moment. Default `public`, control in settings.
  Recorded so it is not re-proposed as new.
- **Operator back-office** (kill a bad invite link, ban a user, review
  suggestions). *Trigger:* a manual task turns frequent or dangerous.
  At this scale almost every admin action is cheaper as a one-off query
  — with the exception of **destructive** operations, which deserve a
  guarded script well before a UI.

One norm worth re-reading rather than acting on: a `private` user sees
everyone's faces while showing none of their own. Probably right — it is
exactly the browse-don't-broadcast person the tier exists for — but it
is a one-way norm. **Revisit if lurking becomes the majority.**

---

## FROM THE SCRAPER 2026-09-09 — the serving view now filters on race status, and `race_tile.html` misreads that column

**`source:` scraper repo, T-037, migrations 070 + 071, ships in 0.63.0.**
Two things, and the second is a bug in this repo.

*PM 2026-10-21:* part 2 is **ticketed W-021** (p4). Part 1 is information,
not work: `list_races` groups whatever rows arrive, so a vanished race is
just one fewer row. The other callers were not checked.

### 1. `core.v_denormalized_event_data_upcoming` can now lose rows

Until today the view rendered every `core.races` row. It now joins
`WHERE r.status = 'active'`, so **a race can disappear from the view
without the event disappearing.** That was not previously possible.

**Day-one diff is not zero, but it is small and intended:** four rows.
Measured either side of the change, 1,795 → 1,791 rows over an unchanged
363 events. The four are slug-variant duplicates that were being served
twice:

```
sportscheck_run_berlin   "10km" + "10 km"        -> "10km" survives
sportscheck_run_berlin   "21,1km" + "21.1 km"    -> "21,1km" survives
sportscheck_run_berlin   "5km" + "5 km"          -> "5km" survives
berlin_half_marathon     "Inlineskating" + "Inline Skating"
                                                 -> "Inline Skating" survives
```

**The skating pair is the one worth knowing about.** Both rows rendered,
with **different 2027 registration prices — 66 and 73**. The surviving
row is the one whose registration answers were written by the more recent
parse, and 73 is now what the page shows, consistent with that event's
other races.

**Going forward the diff is not always zero.** Nothing else is scheduled
to be deactivated — the bulk retirement of discontinued races was
deliberately excluded from that ticket — but the mechanism is live, so
treat "a race that rendered yesterday and does not today" as possible
rather than impossible.

### 2. `race_tile.html` reads `race_status` as a registration signal, and it is a lifecycle column

`app/templates/partials/race_tile.html` line 5:

```jinja
{% set reg_open = race.race_status and 'open' in race.race_status | lower %}
```

**`race_status` is `core.races.status`, whose vocabulary is `active |
inactive | cancelled`** — it says whether a race exists and is served,
not whether registration is open. `'open'` is not a substring of any of
those, so `reg_open` has never once been true: this is dead code today,
and the change above does not trip it, because after filtering this app
only ever sees `active`.

**It is still worth fixing, for the reason it is currently harmless.** If
that vocabulary ever gains a value containing `open`, every tile of that
race lights a false "registration open" badge. The scraper side has
recorded a constraint never to introduce such a value, which protects you
but leaves the misreading in place.

**Registration status lives in the answers, not in `core.races.status`** —
`registration_open` is a question column on the same view. That is the
field this line probably wanted.

---

## Let a user delete their own profile
2026-10-21 · **ticketed W-022** (p3, `tickets/W-022-self-serve-account-deletion.md`). p3 because email already meets Art. 17, but `privacy.html` already promises the button.

A delete button where a signed-in user can delete their own profile.
Today there is no self-serve way out. Note: it is a destructive write
across `web.*` (the user row plus their attendance, auth identities and
crew memberships), so the "guarded before a UI" caution in the
back-office entry above applies here too.

## "Save to calendar" after marking interested / going
2026-10-21 · **ticketed W-023** (p4, `tickets/W-023-save-to-google-calendar.md`). The no-scope hunch is the ticket's first check.

When a user marks themselves interested or going on an event, offer a
"save in calendar" action. **Google Calendar only for now.** A hunch,
not checked: Google's "add event" template link
(`calendar.google.com/calendar/render?action=TEMPLATE&...`) needs no
extra OAuth scope, so it would not touch the sign-in flow.

## New Indie Runners logo assets: main logo, favicon, stock avatars
2026-10-21 · use 2 **ticketed W-024** (p4, waits on the pack). Use 3 + the elaboration below **ticketed W-028** (p4, 2026-10-22, not blocked: inline SVG, no pack). **Use 1 stays raw:** placement is Paulo's call.

There is a new logo asset pack at `static/brand/` (README,
`build_assets.py`, `svg/ir-mark-*.svg`, `favicon/`, `social/og-image.png`),
served as `/static/brand/...`. Its README has suggested `<head>` tags for
`base.html`, written for `/static/favicon/` — use `/static/brand/favicon/`.

Three uses:

1. **Main logo** should go somewhere on the site (where is open).
2. **Browser favicon** — the site has none today.
3. **Community-activity avatars for hidden users / signed-out view** —
   today `avatar--stock` in `partials/avatar_strip.html` is a plain gray
   circle with the text "ir". Replace it with the ir mark. Paulo's view:
   every stock avatar should carry **the same symbol on different
   background colours** (the existing `--avatar-color-0..3` in
   `main.css` are one candidate palette; the pack uses forest #1c2b1e,
   off-white #f6f4f0, amber #e8a44a).

**Paulo's elaboration of point 3, 2026-10-21 (verbatim):**

```text
Task: brand-styled anonymous avatars for logged-out visitors

Goal
When a visitor is not logged in, race tiles and event pages show anonymous
avatar circles for the people who are going or interested. Today these use
the plain .avatar--stock style (sage background). Replace them with
brand-styled anonymous avatars so the rows look varied and on-brand while
still clearly representing real people. This is a nice-to-have polish task,
roughly an hour. Do not change avatars for logged-in visitors.

Design
Each anonymous avatar is a coloured circle with a small runner glyph inside:
an off-white head-and-shoulders silhouette whose head is the amber dot from
the "ir" logo. Use this inline SVG, unchanged:

<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <path d="M5 21c0-3.9 3.1-7 7-7s7 3.1 7 7" fill="none"
        stroke="var(--off-white)" stroke-width="2.6" stroke-linecap="round"/>
  <circle cx="12" cy="8.5" r="3.6" fill="var(--accent)"/>
</svg>

Backgrounds rotate through five colours, defined as CSS variables in
main.css next to the existing avatar palette:
  --anon-bg-0: var(--avatar-color-0)
  --anon-bg-1: var(--avatar-color-1)
  --anon-bg-2: var(--avatar-color-2)
  --anon-bg-3: var(--avatar-color-3)
  --anon-bg-4: var(--forest-mid)
The SVG fills the circle at about 70 percent, centred.

Rules
1. Colour is chosen by the avatar's position in its row (index mod 5),
   never by user id or anything else tied to identity. Logged-out visitors
   must not be able to recognise the same person across races by colour.
   Make sure no user id, name or photo URL ends up in the HTML for these
   avatars.
2. The "+N" overflow circle (.avatar--overflow) stays as it is, neutral.
3. Keep existing sizes: .avatar on tiles, .avatar--lg where used, hover
   faces, and the who's coming anonymous row on the event page.
4. The rendering lives in the web app: CSS modifier classes plus one Jinja
   macro, for example anon_avatar(index, size). No image files, no new
   static assets. Changing the palette later must be a CSS-only change.
5. Accessibility: the SVG is decorative (aria-hidden). Keep or add one
   accessible label per avatar row, such as the existing going count text,
   rather than labelling every circle.

Steps
1. Find every place that renders .avatar--stock or the anonymous rows
   (tiles, tile hover overlay, event page who's coming). List them before
   changing anything.
2. Add the CSS variables and modifier classes (.avatar--anon,
   .avatar--anon-0 to -4) in main.css. Keep .avatar--stock in place until
   nothing uses it, then remove it.
3. Add the macro and use it in all the places from step 1.
4. Add a test that renders a row of anonymous avatars and checks that
   colours follow index mod 5 and that no user identifiers appear in
   the output.
5. Add a CHANGELOG entry.

Done when
- A logged-out visitor sees varied, on-brand anonymous avatars on tiles,
  hover overlays and event pages.
- Logged-in views look exactly as before.
- Tests pass.
```

## Anchor the delete section on /settings (developer, 2026-10-23, while on W-034)
2026-10-24 · **ticketed W-043** (p5).

Terms §9 and privacy §8 both link to plain `/settings`. The delete section
sits at the bottom, so "Settings → Delete account" means scroll to find it.
An `id` on that section (`settings.html:98`) and `/settings#delete-account`
in both links would land the user on it. Kept out of W-034 on Paulo's call:
it touches `settings.html` and is a link nicety, not a defect.

## Two crews can have the same name, and one pair already does
2026-10-23 · **ticketed W-041** (p3, no migration: slug is already UNIQUE; PM answered 1, 2, 4, 5 in the spec; **3, renaming the existing pair, is Paulo's**) · **written from a scraper session on Paulo's behalf; the decision quoted is his**

Paulo: *"can crews created by different people have the same name? It
should not be the case!"*

**Yes, today they can (verified in code).** `web.crews.display_name` has
no unique constraint (`migrations/010_crews.sql`); only `slug` is
unique. `CrewService.create_crew` (`app/services/crew_service.py:30`)
handles a taken slug by retrying with `-2`, `-3` … up to `-11`, so a
second "Crew A" is created silently as `/crews/<crew-a>-2`.
The pages show `display_name`, so the two read identically: on
`/settings`, on the crew page, and on the invite screen ("Join
<name>"). The invite screen is the one that matters: someone who gets
a link cannot tell which crew it is.

**It has already happened (verified, `web.crews`, 2026-10-23, counts
only).** One crew name is held by two crews created by two different
users, identical including case, and the second slug carries a numeric
suffix.

**Questions for the PM or Paulo:**

1. **Unique how?** Compare names ignoring case and surrounding spaces,
   so "crew a " clashes with "Crew A"? Suggest yes:
   compare the slug, which already folds both, and refuse instead of
   suffixing.
2. **Same creator too?** Paulo's words name different people. Suggest
   one rule for everyone: no two crews share a name.
3. **The existing pair.** A unique index cannot be added while two rows
   clash. Rename one (which, and who tells its members?) before the
   migration runs. Migrations need Paulo's approval.
4. **What the user sees.** The `/crews/new` form returns a message
   ("That name is taken") and keeps what was typed, instead of today's
   silent `-2`.
5. **Crews are invite-only with no public directory**, so a refusal
   tells the creator that a crew with that name exists. Acceptable? It
   reveals a name, not its members.

## Crew members' names should link to their profiles
2026-10-23 · **ticketed W-042** (p4; PM: private stays plain text, the row is one link) · **written from a scraper session on Paulo's behalf; the decision quoted is his**

Paulo: *"make peoples profile in listing of members of crews
clickable"*.

**Today (verified in code).** The Members list on a crew page
(`app/templates/crews_detail.html:32-48`) shows each member's avatar and
name as plain text. The "who's coming" list on an event page already
links each name to `/profile/{{ u.id }}` (`event.html:456,476`), so the
pattern and the route exist.

**What a crew-mate would see on clicking** (`profile_service.py`
`_can_view`). Everyone on that page is signed in and shares the crew:

- `public` or `crews_only` member: their profile.
- `private` member: the "hidden" placeholder, the same one a stranger
  gets.
- Yourself: your own profile.

**Paulo on the avatar (2026-10-24):** *"yes"*: the whole row, avatar
and name, is one link.

**What "private" does for a crew member today (verified in code).** The
settings page promises: *"Only you can see your name and past races.
Others still see counts."* That holds on event pages (who's coming,
`attendance_service.py` `_is_identity_visible`), where a private member
is a count even to their own crew-mates, and on their profile, which
shows "hidden" to everyone else, crew-mates included. **It does not
hold on the crew page:** the Members list shows every member's avatar
and name, private ones too, to everyone in the crew. A private member
who joins a crew is named to its members, contrary to the promise.

**Paulo decided (2026-10-24): *"change the settings wording"*.** The
crew page keeps showing private members. The Private option's text
(`settings.html:52-53`) changes to say so, for example: *"Only you can
see your name and past races, except that members of a crew you join
see your name in its member list. Others still see counts."* Separate
from W-042, which settles the link (private stays plain text).

The options Paulo chose between: either the settings wording says crew-mates see your name in the crew's member
list (joining a crew is a choice to be known there), or the list hides
private members' names. The first seems right, since a crew is
invite-only and you join it knowingly, but it is Paulo's call.
(`privacy.html` does not describe the visibility levels, so only the
settings text makes the promise.)

## Recently checked: show the time, not just the date
2026-10-23 · **ticketed W-039** (p2, the next ticket) · **Paulo, high priority: close the stats-page topic soon**

Paulo: *"it would be great to include timestamps to the recently
checked."* Clock decided by Paulo: **UTC**, labelled.

**Today (verified in code).** `app/templates/stats.html` prints
`checked_at.strftime('%-d %b %Y')`, date only. The value is a
`timestamptz` rendered in the DB session's `TimeZone`, which nothing in
`app/db.py` sets: the W-025 verdict's open "renders in UTC" item. With a
time on screen, a wrong zone becomes visible, so convert to UTC
explicitly rather than trusting the session.

## Link Indie Runners' Strava club and Instagram from the site
2026-10-24 · **Paulo: priority 3** · **ticketed W-046** (p3, PM 2026-10-26): two text links in the footer, no icons.

Paulo: *"please put links to the strava profile and instagram account of
indie runners in the website."* Instagram:
https://www.instagram.com/weareindierunners/ · Strava club:
https://www.strava.com/clubs/2244858

## Same-day races show a date range
2026-10-24 · **Paulo** · **ticketed W-047** (p3, the next ticket, PM 2026-10-26). Only the event page hero has it (`event.html:55-56`); index tiles already show one date.

Sometimes, all the races are on the same day, and the web displays dates
as 29 May – 29 May. In the case where all races are on the same day, only
one date should be displayed, not a range.

## A drift check for `core.py` against the view
2026-10-25 · **Paulo, at W-014** · **ticketed W-048** (p4, PM 2026-10-26). Run by hand, not from `deploy.sh`: that would make every deploy a DB session, and CI can't reach the DB.

W-014 is a one-off audit, true on the day it ran. The scraper owns the
view and keeps changing it (a 55th column on 2026-09-09; this repo
found out only because a ticket needed it). Proposal: a small script
that runs W-014's `information_schema` query, compares it to
`Race.__table__.columns`, and exits non-zero on a missing column, a changed
type or an unmapped one. It needs no test suite, so it doesn't wait on W-003. It could
run from `deploy.sh`, or whenever the scraper changelog mentions the view.

## infra I-006 2026-10-26 — W-018's mapping step becomes a Terraform plan

2026-10-26 · source: infra-audit (indie-runners-infra I-006, filed by its PM) · **PM 2026-10-26: both amendments made.** W-018 step 2 is now the plan. W-008 now says the infra `ignore_changes` on labels goes first, and Paulo routes it (I-006 is already applied, so W-008 lands after it).

W-018 step 2 says to remove the `beta.indierunners.co` Cloud Run domain
mapping in the Console. `indie-runners-infra` I-006 imports all three
mappings into `web/`. It deliberately leaves `prevent_destroy` off the
beta one, so W-018 can remove it through a plan. Once I-006 is applied,
a Console removal reads as drift there. Suggested amendment to W-018:
step 2 is "delete the beta mapping block in `indie-runners-infra/web/`,
plan, apply on Paulo's word", an infra change with W-018 as its reason.
The OAuth URI (step 1) and DNS (step 3) stay operator work, unchanged.

Also for the web PM: I-006 reduces `scripts/deploy.sh`'s
`gcloud run deploy` to `--image` plus `--region`/`--project`/`--platform`.
Every shape flag moves to `indie-runners-infra/web/`. W-008 (open)
adds `--labels=commit=…`. If W-008 lands first, I-006 keeps that flag and
ignores the label in Terraform. If it lands after, it adds the flag to
the reduced script, and the infra side needs the same `ignore_changes`.
Either way W-008's acceptance should name `indie-runners-infra/web/`.

## 2026-10-26 — Footer: Strava and Instagram logos instead of words

2026-10-26 · source: Paulo, after W-046 merged · **ticketed W-050** (p3, PM 2026-10-26). It is second in line, after W-049's 500.

> "could we show the actual instagram and strava simbols instead of saying
> strava instragram? I would like for them to go below the indie runners
> imprint privacy terms"

## infra triage 2026-10-26 — `deploy.sh` still pushes to `gcr.io`; the web's own registry is empty

2026-10-26 · source: infra-audit (indie-runners-infra triage, PM) · **ticketed W-053** (p4, PM 2026-10-26). Retiring `gcr.io` stays with infra and waits on the rollback window (see the ticket's out of scope).

`indie-runners-infra` I-002 created a `web` Artifact Registry repo in
`europe-west1` (output `web_registry`) for the web's images. Moving the
push there was left to this repo (I-002, out of scope):

> **Moving the web deploy off `gcr.io`.** This ticket creates the
> registry; switching `deploy.sh` to push there is the web repo's change,
> in its own ticket. Retiring the `us` `gcr.io` repo follows that, not
> this.

`scripts/deploy.sh:44` still reads:

```
IMAGE="gcr.io/$PROJECT/$SERVICE"
```

On 2026-10-26 the `web` Artifact Registry repository existed in
europe-west1, empty; images still go to `gcr.io`.

The switch only touches this repo. `indie-runners-infra/web/` ignores
the service's image, so a new registry path plans as nothing there. The
image would live in the same region as the service, not in multi-region
`us`. `gcr.io` can't be retired on the infra side until this moves.
Another undeclared service pulls from it too, but that's infra's
problem.

## infra triage 2026-10-26 — `docs/IMAGING.md` lists two tiles-bucket grants that don't exist

2026-10-26 · source: infra-audit (indie-runners-infra triage, PM; from infra I-007's DEV_NOTES) · **ticketed W-056** (p5, PM 2026-10-27). Docs only; the grants stay infra's.

`docs/IMAGING.md:476-479` says `indie-runners-web-tiles` grants Storage
Object Admin to `paulo@indierunners.co` and to the web SA. The live
policy has neither (checked 2026-10-26): it grants only public read
(`allUsers` as object viewer) beyond the project-level defaults.

Local publish runs under the operator's own account. Since infra
I-007 (applied 2026-10-26T21:43Z), the web SA holds no storage role at
all. `indie-runners-infra/web/tiles.tf` declares only the `allUsers`
viewer. The doc is the defect. If a service-side publish is ever wanted,
the grant is a change to `indie-runners-infra/web/`, not a hand grant.

## infra triage 2026-10-26 — W-053's push grants, measured: it works today only through project Editor

2026-10-26 · source: infra-audit (indie-runners-infra triage, PM; answers W-053's "Grants are unverified") · **PM 2026-10-27: W-053 amended.** The grants are quoted in its evidence, and acceptance 1 now says what a failure after I-008 means. No new ticket: the replacement build identity is infra's to route.

`scripts/deploy.sh:83` runs `gcloud builds submit --tag "$IMAGE"` with no
`--service-account`, so the build runs as the project's default build service account,
which can push only through a broad project-level role.

The `web` repo has no repo-level bindings. The push should succeed via
the compute SA's project Editor, and the pull via `run.serviceAgent`.
That comes from the role definitions and hasn't been exercised. W-053's
push-without-deploy is still the test.

**Coupling:** infra I-008 narrows that service account's role. When that
happens, this push loses its grant, and so does today's push to
`gcr.io`. Infra will route the replacement (a build identity and its
grants) as a change in `indie-runners-infra`. It may come with a
`deploy.sh` line (`--service-account`) in the same ticket. Don't hand-grant.

## 2026-10-27 — developer, while on W-013: a TBC page now shows the website link twice
*PM 2026-10-28: **dropped** — Paulo, same day: keeping both is fine for now. Routed check 26 already reads the second link as by design.*

Signed in, a TBC event (`marcs_backyard_ultra/2027`) shows "Official website →" in the action card,
then "Visit the official website →" as a button in the locked panel just below it. W-013 kept the
second one on purpose. Whether one of them should go is Paulo's call.

## infra triage 2026-10-27 — W-057's identities are infra I-015

2026-10-27 · source: infra-audit (indie-runners-infra triage, PM; answers W-057 prerequisite 2) · **PM 2026-10-28: folded into W-057** (spec amended; still GATED on I-015)

Infra **I-015** (`web/`, `deploy: immediate`, the next infra ticket)
adds both identities. Infra merges and applies first.

- **Push SA:** `roles/artifactregistry.writer` on the `web` repository
  only. `workloadIdentityUser` goes to the repo-wide principal set.
- **Deploy SA:** a role on the `indie-runners-web` service, not the
  project, with `run.developer` as the ceiling. The infra developer
  measures it against `deploy.sh`'s `describe` and `run deploy`. It also
  gets `serviceAccountUser` on `indie-runners-web@` only.
  `workloadIdentityUser` is bound to the subject
  `repo:indie-runners/indie-runners-web:environment:production`. A job
  without `environment: production` gets no deploy credentials.
- Both emails become `web/` outputs, for prerequisite 3's `vars.*`.

Left to W-057, and named in I-015's out of scope:

- **The Cloud Run pull from `web`** rides on `run.serviceAgent` and is
  unexercised. W-057's first deploy is the test. A failure there routes
  back as an infra change, never a hand grant.
- **Tag overwrite.** Any branch's job can push as the repo-wide push
  SA, so it can re-point a tag that the gated deploy later names.
  Deploying by digest closes that on your side. Immutable tags on `web`
  would be an infra `platform/` ticket if Paulo wants them.

Infra I-013 shrinks to measuring the compute SA's Editor once W-057 has
shipped a release. No build SA is coming.

## infra triage 2026-10-27 (2) — Paulo's rulings that land on the web: traffic, labels, tags

2026-10-27 · source: infra-audit (indie-runners-infra triage, PM; Paulo's answers in the infra PM session) · **PM 2026-10-28: 1 → ticketed W-068 (p4); 2 → W-008 amended, waits on I-016's answer here; 3 → W-057 amended (I-017 applied, digest deploy); 4 → absorbed, already the triage rule**

**1. Traffic is the deploy's (infra I-009, option B).** `web/` will
ignore `traffic` the way it already ignores the image, so the rollback
that `deploy.sh` prints stays one command and no apply undoes it. Paulo
wants the gap this leaves (a forgotten pin) closed **here**, as a web
ticket. `deploy.sh --check` should print the traffic split. A deploy
should refuse when traffic isn't on the latest revision, unless a flag
says the pin is intentional. That's the same pattern as the scraper's
`deploy_state.py`.

**2. W-008's label: infra I-016 goes first.** Paulo: the label goes on
the **revision**, so infra ignores `template[0].labels`. W-008 says
`--labels=commit=…` and leaves the attribute to infra. **Before either
ticket lands, name the flag here.** If `gcloud run deploy --labels`
also writes service-level labels, either infra ignores both or W-008
uses a revision-only flag. I-016's developer quotes `--help` and
answers here.

**3. Tags become immutable on `web` (infra I-017), and W-057 deploys by
digest.** Paulo: *"Not optional. Fix it, and fix it twice."* I-017
applies before W-057's first push. After that, the registry refuses a
push to an existing tag, so `cd.yml` pushes version tags only and never
a moving one such as `latest`. W-057's gated job resolves the tag to a
digest, deploys `…@sha256:…`, and prints both in the run log for the
approver. Infra I-015 gives the deploy SA `artifactregistry.reader` on
`web` for that. Don't restrict which branches may push (Paulo).

**4. Routing.** W-008's infra ask lived in this repo's backlog note,
which infra triage doesn't read. Infra only found it because Paulo
asked. Send cross-repo asks as an entry in
`indie-runners-infra/docs/IDEAS.md`, with the sender header, as W-057's
was.

## 2026-10-28 — "Who's coming": private attendees show as "and 1 other"
*PM 2026-10-28: **ticketed W-066** (p3, after W-065). Signed-in tier only; the anon row's count is W-063.*

when there is one private user who is going, it shows as "and 1 other" . 

Who's coming
Going

and 1 other
Interested

    Paulo Morales Castillo


whenever there is only one person, a particular message should be shown. jJSomthing like 1 indie runner is going. when there are 2 privates, then 2 indie runners are going. where there is one public and 2 privates, then e.g. juan castillo and 2 other indie runners are going. 

## 2026-10-28 — Footer: add GitHub next to Strava and Instagram
*PM 2026-10-28: **ticketed W-067** (p3). Paulo, same day: ship it; an empty org page until the public flip is fine.*

next to the strava, instagram symbols, include github and the link to our github organization: https://github.com/indie-runners

## infra I-015 review 2026-10-28 — the push identity matches any job in the repo, fork-triggered ones included once it's public
*PM 2026-10-29: **amended W-057** (acceptance 1): `id-token: write` on `cd.yml`'s two jobs only, none in `ci.yml`, no `pull_request_target` workflow. Narrowing the binding stays infra's.*

2026-10-28 · source: infra-audit (indie-runners-infra I-015 review, PM; for W-057) · raw

Infra I-015 (in review) binds the push SA `indie-runners-web-push`
(`artifactregistry.writer` on `web`) to the whole repo, on Paulo's
ruling:

```
resource "google_service_account_iam_member" "web_push_wif" {
  service_account_id = google_service_account.web_push.name
  role               = "roles/iam.workloadIdentityUser"
  member             = data.terraform_remote_state.platform.outputs.principal_sets["indie-runners-web"]
}
```

That member is
`principalSet://…/workloadIdentityPools/github/attribute.repository/indie-runners/indie-runners-web`.
Once the repo is public, any workflow run in it that gets
`id-token: write` can push. That includes a `pull_request_target`
workflow that checks out a fork's code. Immutable tags (infra I-017,
applied) stop it overwriting a tag, but not pushing a new one. The
deploy SA is unaffected: it's bound to
`repo:indie-runners/indie-runners-web:environment:production` alone.

For W-057's spec: give `id-token: write` only to `cd.yml`'s jobs, and
don't add a `pull_request_target` workflow that requests it. Narrowing
the binding instead (to a ref or a workflow) would be a `web/` change
in infra.

## 2026-10-30 — Stats page: "checked" is unclear to users
2026-10-30 · raw
*PM 2026-10-31: **ticketed W-083** (p3, after the crews arc). The three `##` lines below are Paulo's draft headings inside this entry, not separate entries.*

elaborate more on the stats page, at the moment we read

493 events tracked

Every event Indie Runners follows, whether or not it has a date coming up.

278 events checked in the last 30 days

Upcoming events whose details we went back and looked at.

I got feedback from users that the word checked is not clear. Maybe elaborate more on it. 


## 493 events tracked

This is the total number of events we look at and follow at indie runners. Whether or not it has a date coming up. -- notice lower case

## 278 events checked in the last 30 days

We fetch information from all the event we follow on a constant basis, so that we can keep you up to date with what is going in. 

## Upcoming events whose details we went back and looked at...

on the same idea, the list of countries comes ranked (enumerated) below the map. Please remove the rank and simply list the countries alphabetically. So instead of having numbers, just two columns with the list of countries alphabetically, with their respective numbers.

## 2026-10-30 — Mobile: race details hidden when the index tile is tapped
2026-10-30 · raw
*PM 2026-11-04: **ticketed W-107** with the 2026-11-04 hover-panel entry, the same overflow. Ranking the fields stays open: if W-107's default isn't enough, its developer brings Paulo a screenshot.*
*PM 2026-10-31: **left raw.** This is a question about what to show, and the PM can't rank fields it hasn't seen overflow. Settled by: a 375px screenshot of a tapped tile that overflows, listing its fields in order. Paulo then picks what goes first and what drops. That becomes the ticket.*

when the index tile is clicked on, while on mobile, the information on the race comes up, but often times it hides out because there is already a lot. What should we prioritize so that everything fits?

## Sharpen the wording of the three visibility levels
2026-10-31 · raw · **written from a scraper session (analyst) on Paulo's behalf; the wording quoted is his**
*PM 2026-10-31: **ticketed W-076**, with Crews v1 decision 1. That decision makes it two levels. Point 1: Paulo's "other indie runners" is accurate (signed-in only). Point 2 lapses with `private`. Point 3 defaults to keeping the counts clause, for Paulo to confirm. Label "Open", value stays `public`.*

Paulo wants each level described in one plain sentence about **your
calendar**, in his words:

- *"open - your calendar is visible to other indie runners"*
- *"crews only - your calendar is visible to your crew"*
- *"private - your calendar is visible to only you"*

**Today (verified in code).** The same three levels are described in
two places, with different nouns:

- `app/templates/settings.html:35,44,53` (the radio buttons): "your
  name and past races", plus "Others still see counts".
- `app/templates/profile.html:71,73,75` (the banner on your own
  profile): "your profile and race calendar", plus "Everyone else still
  sees attendance counts".

The label is **Public** in both, not "Open"; the stored value is
`public` (`profile_service.py` `_can_view`). Whether the label becomes
"Open" is part of this idea. *Hunch:* renaming only the label is a
template change; the value can stay `public`.

**Three things the PM should settle with Paulo before ticketing:**

1. **"Other indie runners" means signed-in users.** `_can_view` shows
   nothing to a signed-out visitor, even for a `public` profile, and
   the profile banner says so ("Signed-out visitors cannot"). Paulo's
   sentence is accurate if "indie runners" means people with an
   account. *Verified in code.*
2. **"Visible to only you" contradicts a decision Paulo made on
   2026-10-24** (entry "Crew members' names should link to their
   profiles", above). The crew page's Members list shows a `private`
   member's name to everyone in that crew, and Paulo chose *"change the
   settings wording"* to admit it, rather than hiding them. The
   proposed sentence talks about the **calendar**, and the calendar
   really is hidden from crew-mates (`_can_view` returns false for
   `private`). So it holds if it is read as "your calendar", but a
   private member's **name** is still visible in a crew they join.
   *Verified in code.* That 10-24 wording change has **not shipped**:
   `settings.html:53` still says "Only you can see your name", and
   W-042 does not carry it. *Verified, as of `7d750a8`.* Both wording
   changes belong in one ticket.
3. **Counts.** Both pages today add that others still see attendance
   counts. Paulo's sentences leave it out. Whether to keep that clause
   is his call; dropping it makes "private" sound stronger than it is.

## scraper-analyst 2026-10-30 — leaving a crew, and removing someone from one
2026-10-30 · raw · **source: `indie-runners-scraper` analyst, written on Paulo's behalf in that repo's `docs/IDEAS.md` (2026-10-30; the decisions quoted are his, everything else is the analyst's reading). Carried verbatim by the scraper PM, triage 2026-10-31.**
*PM 2026-10-31: **ticketed W-081** (leave) and **W-082** (an admin removes someone), per Crews v1 decision 2. Defaults for the four open points are in those specs: hand over on the last admin's exit, an admin may remove an admin, no auto-rotate, no notice.*

Paulo: *"allowing the possibility for users to leave a crew, and for crew admins to remove someone from the crew"*.

Two features: a member leaves on their own, and an admin removes a member. Everything below is the analyst's reading of the web repo at its checkout on 2026-10-30, not Paulo's direction.

**Today neither exists** (verified). The only crew routes in `app/main.py` are `/crews/new` (GET, POST), `/crews/{slug}` (GET), `/crews/{slug}/invite/rotate` (POST) and `/crews/join/{token}` (POST). `CrewService` has `add_member` and no method that removes one. The only way out of a crew is deleting the whole account.

**What the work must not get wrong** (verified from the code):

- **`web.crews.created_by` and `web.crew_invites.created_by` are soft refs with no FK.** Deleting the membership row does not touch them. W-022's spec says so already: *"no route lets a creator leave their crew. A future 'leave crew' or 'remove member' ticket makes it reachable and must hand over `created_by` itself."* If a creator leaves and `created_by` is not handed over, `UserService.delete_account` hits its leftover-reference check if that person later deletes their account (`user_service.py`, the `leftover` count), rolls back and returns a 500.
- **A rule for handing a crew over already exists.** In `delete_account`, the crew passes to the longest-standing remaining member, admins first (`ORDER BY role='admin' DESC, joined_at ASC`), and that person is promoted to `admin` and given `created_by` on the crew and its invites. If nobody else is in the crew, it is deleted. Reusing that rule for "leave" keeps both ways out of a crew behaving the same.
- **A removed member can come straight back.** The invite link has no expiry and can be used more than once, and the removed person may have it. Removing someone does not stop them rejoining unless the link is also rotated (admin-only, and it already exists). (believed: from `ARCHITECTURE.md` § Crews; the join path was not traced)
- **Removal changes who can see whom, immediately.** `crews_only` visibility means "shares at least one crew" (`ARCHITECTURE.md` § Crews). A removed member stops seeing the crew's `crews_only` attendees, and they stop seeing them, unless the two share another crew. That is the intended effect, and a test should pin it.

### For Paulo to decide

1. **The last admin leaves:** hand the crew over by the same rule as account deletion, or refuse until they promote someone? Promoting by hand does not exist yet either.
2. **Can an admin remove another admin?** The roles are only `admin` and `member` (CHECK constraint), and more than one admin is possible.
3. **Rotate the invite link automatically when someone is removed**, or leave that to the admin?
4. **Does the removed member find out?** The app sends no notifications, so today they would just see the crew page as "hidden".

### Unexplained / not checked

- How many crews have more than one member, or more than one admin. Not measured; the database was not queried.
- Whether the join route blocks a removed user. It cannot today, because nothing records that someone was removed.

## scraper-analyst 2026-10-30 — a crew digest by email, and a crew hub with a shared calendar
2026-10-30 · raw · **source: `indie-runners-scraper` analyst, written on Paulo's behalf in that repo's `docs/IDEAS.md` (2026-10-30; the decisions quoted are his, everything else is the analyst's reading). Carried verbatim by the scraper PM, triage 2026-10-31.**
*PM 2026-10-31: **hub half → the Crews v1 tickets (W-077 onward). Digest half left raw.** Notifications are in v1's Out list. Settled by: v1 shipping, then Paulo's answers to the six questions below, plus a privacy-page decision on the new purpose. Its scheduler would route to infra.*

Paulo: *"An email notification system that would inform the members of a crew updates regarding their crew plans. I am thinking, an email subscription automatically that crew members are able to opt out of. Summary about recent activities, like John is going to the berlin marathon, etc. This emailing system should be used for other purposes later on. At the same time, there should be a crew hub where members of a crew can always look at a shared calendar from members of the crew. I am thinking, this update should come every x days, or on a particular day of the week, assuming there have been updates at the crew level."*

Three pieces, in his words: (1) a general email-sending capability, built for reuse; (2) its first use, a crew digest — automatic subscription, opt-out, sent every N days or on a weekday, and only when the crew had activity; (3) a crew hub page with a shared calendar of the members' races. Everything below is the analyst's reading of the web repo at its checkout on 2026-10-30, not Paulo's direction.

**What exists today** (verified):

- **The app sends no email at all.** No mail library in `requirements*.txt`, nothing in `app/` that sends one. `web.users.email` is there (nullable, unique) from Google sign-in, so addresses exist.
- **The web app has no scheduled job.** It is one Cloud Run service (`indie-runners-infra/web/*.tf`: `service.tf`, no job, no scheduler). A digest needs a trigger; the scraper side already runs Cloud Run Jobs on Cloud Scheduler, so the pattern exists in the other repo and in infra.
- **The crew page is a member list and an invite link** (`crews_detail.html`: sections "Members" and "Invite link"). No races, no calendar. The data for a shared calendar is already there: `web.attendance` (`user_id`, `event_id`, `occurrence_id`, `status` going|interested) joined to `core.*` the way `ProfileService` already builds a runner's upcoming timeline.
- **`web.attendance` has `created_at` only, no `updated_at`**, and `mark_attendance` changes an existing row in place (`existing.status = status`). So "what happened since the last digest" cannot be read from the table as it is: a switch from interested to going leaves no trace of when. Either an `updated_at` column, a small activity log, or the digest compares against what it last sent.
- **The settings page has no email or notification section** — the opt-out needs a new knob next to the visibility radio.

**What the work must not get wrong:**

- **Privacy comes first, and the rules already exist.** A member set to `private` is hidden from everyone but themself; `crews_only` shows to crew-mates; `public` to any signed-in viewer (`ARCHITECTURE.md` § Visibility). A digest or calendar is a new viewer surface and has to apply the same predicate, otherwise a `private` runner's race is mailed to the whole crew. The small-crew hint on the crew page (under 4 members, the count reveals the person) applies to the digest too, more so: a named line "John is going to Berlin" is exactly the identification the hint warns about, so it should only ever name people whose visibility allows it. (verified: the predicate; believed: that nothing else gates it)
- **Opt-out has to be real, in the mail and in settings**, and the sender address, SPF/DKIM and the privacy page (which lists what the app does with the email address) all change. `privacy.html` says what the address is used for today; a digest is a new purpose and has to be written in before the first send.
- **"Only when there were updates"** is the hard part, per the `created_at` point above.
- **Reuse over bespoke:** Paulo wants the sender used for other things later. The smallest shape is one function that takes a recipient, a subject and a rendered template, backed by a transactional provider; the digest is one caller.

### For Paulo to decide

1. **Provider:** a transactional email service (SendGrid, Postmark, Resend, Mailgun, SES) or Gmail/Workspace SMTP from the `indie-runners` domain. The free tiers of the first group cover the current user count many times over; the choice is mostly who holds the DNS records.
2. **Cadence:** fixed weekday (one send, e.g. Monday morning) or every N days per crew. A weekday is simpler to run and to explain in the email itself.
3. **What counts as activity:** new going/interested marks only, or also changes and removals ("Anna is no longer going").
4. **Opt-out scope:** per crew, or one switch for all crew mail. One switch is the smallest.
5. **Is the hub the existing `/crews/{slug}` page grown a calendar**, or a separate page? The hint, members and invite already live there.
6. **Trigger:** a Cloud Run Job + Cloud Scheduler in infra (the scraper's pattern), or an endpoint the scheduler calls on the service.

### Unexplained / not checked

- How many users have a non-null `email`, and how many crews have more than one member. Not measured; the database was not queried.
- Whether Google sign-in's `email_verified` gate means every stored address is deliverable. Believed yes, not checked.
- Whether a digest counts as marketing under the consent rules the privacy page is written to, or as a service message. Not a legal read; the PM may want one before the first send.

## scraper-analyst 2026-10-31 — Crews v1: the hub spec, and what it depends on in each repo
2026-10-31 · raw · **source: `indie-runners-scraper` analyst, written on Paulo's behalf in that repo's `docs/IDEAS.md` (2026-10-31; the decisions quoted are his, everything else is the analyst's reading). Carried verbatim by the scraper PM, triage 2026-10-31.**
*PM 2026-10-31: **`docs/PLAN.md` rewritten around it.** Tickets W-076 to W-082, after W-072's review. Nothing on the board blocks it beyond W-072. W-042 is folded into W-080, and W-031 is amended.*
*PM 2026-11-01: **build step 3 (the hub's Going | Interested control) dropped.** Shipped as W-079, reverted the same day. Paulo: "It did not make sense to have these buttons." Members mark races from the event page.*

**Carrier's note (scraper PM).** Paulo ranks this first: *"This has the highest prio until it is done, if there are open tickets that need to be done before, then those go higher in prio."* Nothing on the scraper board has to land first: the analyst's measurement below (63% of next-12-month occurrences dated, 0 with neither date nor month) found no blocking scraper ticket, and the scraper PM agrees. One scraper fact the hub inherits: `core.event_occurrences` is `UNIQUE (event_id, year)`, so an event with two editions a year (EcoTrail Paris, spring and autumn) has one occurrence row and the hub will show one row. That is a `core.*` direction question, left raw on the scraper side. It does not block the hub. Decision 1 below (*"collapse to two level only"*, `private` goes) is Paulo's latest word on visibility. It overrides any wording entry that still describes three levels.

Paulo's priority, in his words: *"This has the highest prio until it is done, if there are open tickets that need to be done before, then those go higher in prio."* And on who orders the work: *"I do not know what dependencies we have from scraper and from web, and I do not know who should decide that, whether you or PM."*

**Who decides** (from `docs/roles/README.md` and `analyst.md`): this entry records the dependencies with evidence; it does not rank. Our PM carries it to `indie-runners-web`'s `docs/IDEAS.md` (the only courier in that direction). The web PM cuts tickets and orders them, applying Paulo's rule above: anything listed under "Dependencies" that has to land first goes ahead of the crew tickets.

### The spec, verbatim (Paulo's; agreed 2026-10-31)

> # Crews: spec for first version
>
> Status: agreed 2026-10-31, ready to build.
> Design reference: Claude Design canvas "Crew hub sketches", artboard D.
>
> ## Outcome
>
> A runner who joins a crew can see, in under a minute, which races the crew is converging on over the coming months, and can add themselves to the plan from that page. Crews are also the invite loop: a member shares a link, a friend opens it, signs in with Google, and lands on the hub.
>
> ## Scope of this version
>
> In:
> - Create a crew
> - Join a crew via invite link
> - Leave a crew
> - Crew hub page, visible to members only
> - My crews listed on the user profile page
>
> Out (do not build):
> - Roles, admins, approval of members
> - Per crew settings or per crew visibility of attendance
> - Email invites
> - Notifications
> - The "who is where" matrix view (artboard C)
>
> ## Rules
>
> 1. A user can belong to many crews. Schema is many to many from day one.
> 2. Attendance is global. A user marks going or interested on a race occurrence once, and every crew they belong to sees it. Attendance is never crew scoped.
> 3. The hub is a read over existing attendance data, filtered to crew members. Attendance buttons on race pages do not change.
> 4. Access check is a single rule: the current user is a member of this crew. Nothing else.
> 5. If someone does not want a crew to see their plans, they leave the crew.
>
> ## Data model (web schema)
>
> ```
> crew
>   id            serial pk
>   name          text not null
>   slug          text not null unique
>   created_by    fk user
>   created_at    timestamptz
>
> crew_member
>   crew_id       fk crew
>   user_id       fk user
>   joined_at     timestamptz
>   pk (crew_id, user_id)
>
> crew_invite
>   token         text pk
>   crew_id       fk crew
>   created_by    fk user
>   created_at    timestamptz
>   expires_at    timestamptz nullable
> ```
>
> One invite token per crew is enough for now. Regenerating replaces it.
>
> ## Routes
>
> ```
> GET  /crews/new                 form to create a crew
> POST /crews                     create, add creator as member, redirect to hub
> GET  /crews/{slug}              hub, 404 if not a member
> POST /crews/{slug}/leave        remove membership, redirect to profile
> GET  /join/{token}              if not logged in, start Google OAuth and return here
>                                 if logged in, add membership if missing, redirect to hub
> POST /crews/{slug}/attendance   see Attendance below
> ```
>
> Profile page gains a "My crews" section: crew name, member count, link to hub, button to create a crew. If a user has exactly one crew the nav link "Crews" goes straight to that hub, otherwise to the profile.
>
> ## Hub page (artboard D)
>
> Layout: two columns. Left is the agenda, right is a sidebar. On narrow screens the sidebar stacks below the agenda.
>
> Header: crew name, label "Crew hub".
>
> Agenda column:
> - Toggle: "Going only" / "Going and interested". Default is going and interested.
> - Legend: solid chip means going, dashed chip means interested.
> - Races grouped by month, ascending, starting from today. Each race row shows:
>   - date block (day number, weekday)
>   - race name linking to the race page, location, distance
>   - name chips for every crew member who marked it: solid for going, dashed for interested
>   - the current user's attendance control (see below)
> - Only occurrences that at least one member has marked appear. Past occurrences do not appear.
> - When "Going only" is active, rows with no going members are hidden and interested chips are hidden.
>
> Sidebar:
> - Members box: list of members with initials avatar, name, and "Next: {race}, {date}" being their soonest going race, or "Nothing confirmed yet".
> *PM 2026-11-02: the "Next:" clause is **dropped by Paulo** ("we do not want that"); W-080 amended to profile links and invite wording.*
> - Invite box: readonly input with the invite URL and a Copy button. Short explanation: share this link in your group chat, anyone who opens it and signs in joins the crew.
> - Leave crew button.
>
> ## Attendance control on the hub
>
> Two segment control per race row: [Going | Interested].
> - Neither filled: user has no attendance on this occurrence.
> - One filled: that is the user's current status.
> - Clicking the other segment switches status.
> - Clicking the filled segment clears status.
> - There is no separate remove button.
>
> Backend rule: if the posted status equals the current status, delete the attendance row; otherwise upsert. Expose this as a toggle method on the attendance service so the race page could use the same logic later. The race page keeps its current "change / remove" pattern in this version.
>
> After the post, re-render the row (htmx partial if available, otherwise full page redirect back to the hub).
>
> ## Queries
>
> Hub query, one statement: crew members join attendance join occurrences join races, where occurrence date >= today, ordered by date. Group into months in Python, not SQL.
>
> Members box "next race": for each member, min occurrence date where status = going and date >= today. Can be derived from the same result set as the hub query, no second query needed.
>
> ## Build order
>
> 1. Tables and models, migration
> 2. Create crew, profile section, hub with agenda only (no sidebar, no attendance control)
> 3. Attendance control on hub rows, toggle method on attendance service
> 4. Members box
> 5. Invite token, join route, invite box
> 6. Leave crew
>
> Each step is shippable on its own.
>
> ## Before starting
>
> Run one query against core: what share of race occurrences in the next twelve months have a confirmed date. If it is low, the hub will look empty and the first ticket belongs to the scraper, not here.
>
> ## Open decisions (not blocking)
>
> - Whether the segmented control later replaces change / remove on the race page.
> - Whether the "next up" hero from artboard B is added above the agenda if the page feels thin.

Everything below is the analyst's reading, of the web repo at its checkout on 2026-10-31 (`7d750a8`) and of live Cloud SQL (read-only, 2026-10-31), not Paulo's direction.

### The spec is written as if crews are new. Most of it is already live

(verified, from `indie-runners-web` source)

- **Tables exist, in a different shape.** `web.crews` (`display_name`, not `name`), `web.crew_memberships` with a `role` column (`CHECK role IN ('admin','member')`), `web.crew_invites` with `revoked_at` (rotation keeps history; it doesn't replace the token) and no `expires_at` (`app/models/web.py:72-117`). Many to many already. **Build step 1 is not a migration.** It is a decision about whether the spec's model replaces the existing one (see "For Paulo to decide").
- **Create, join by link and the member-only crew page exist.** `GET/POST /crews/new`, `GET /crews/{slug}` (member list + invite link, `crews_detail.html`), `POST /crews/{slug}/invite/rotate` (admin only), `GET /crews/join/{token}` (confirm page; signed-out goes to Google and back) + `POST` (accept) (`app/main.py:694-832`). So build steps 2 (create) and 5 are mostly done.
- **What is actually new:** the agenda on the crew page, the toggle control and a `toggle` method on `AttendanceService`, the members box's "Next: …", leaving a crew, a "My crews" block on `/profile` (today the crew list is on `/settings`, `main.py:627`), and a "Crews" nav link (the nav has My profile and Settings only, `base.html:42-43`).
- **Where the routes differ from the spec:** `POST /crews/new` not `POST /crews`; `/crews/join/{token}` with a confirm step, not `GET /join/{token}` joining on GET; a non-member gets `crews_hidden.html` (200, no crew name), which is deliberate (`main.py:742`, "PLAN Decision 10"), not a 404. The app has no htmx (no match in `app/templates` or `static/`), so the spec's fallback applies: a full redirect back to the hub.

### Rule 2 overrides the `private` setting. This blocks the hub

(verified: the predicate and the counts. The privacy-page wording was read only in `settings.html`/`profile.html`.)

Today a user picks `public`, `crews_only` or `private`, and `_is_identity_visible` (`attendance_service.py:33-48`) shows a `private` attendee to nobody but themself, crew-mates included. Rule 2 ("every crew they belong to sees it") and rule 5 ("they leave the crew") mean a hub that shows `private` members' races to their crew. Live data (counts kept private): **every `private` user is in a crew**. So the very first hub render would show races that people currently have marked as hidden from everyone.

Two ways to build it: (a) the hub applies the existing predicate, so a `private` member's chips never render and their "Next:" reads "Nothing confirmed yet"; or (b) crews override `private`, and the settings text, the privacy page and those three users are dealt with before the hub ships. The 2026-10-30 digest entry above raised the same question for email.

### Dependencies, web side

Facts the web PM orders by, not a ranking.

- **W-072 is being built** (worktree `irw-W072`, commit `62cf9e1` "lock attendance the day after an edition's last known day; both routes refuse (1.9.49)"). It changes `mark_attendance`/`clear_attendance`, and the spec's toggle method wraps exactly those two. **The toggle has to land on top of W-072.** (verified: the commit; believed: the overlap, the W-072 diff not read)
- **W-031 (open, p4):** every POST except account deletion trusts SameSite alone. The spec adds two more (`/leave`, `/attendance`), and one-step `GET /join` would be a GET that writes, which W-031's Origin check can't cover. (verified: the ticket row)
- **Leaving a crew (step 6) carries the 2026-10-30 "leaving a crew" entry's trap:** `created_by` on crews and invites is a soft ref with no FK, so a creator who leaves without handing it over makes their later account deletion fail its leftover check and return a 500. Dropping roles from the spec doesn't remove that; the hand-over rule from `delete_account` can be reused. (verified there on 10-30, not rechecked)
- **W-019's lesson applies to the hub's race links.** The event page 404s once an edition leaves the serving view. The hub shows future rows only, but the link should use the same guard the profile uses. (believed)
- **Attendance is per event occurrence and has no `race_id`** (`web.attendance`: `event_id`, `occurrence_id`, `status`, `race_date`, `event_display_name`). The spec's "race name … distance" per row has no single source. A row is an edition of an event, and "distance" means the event's list of races. (verified)
- Open crew tickets in the same templates: W-042 (member names don't link to profiles), W-052 (crew name over 120 chars returns a 500). (verified: board rows)

### Dependencies, scraper side, and the "before starting" number

No scraper ticket blocks the first build. (verified for the number, believed for "blocks")

Live, 2026-10-31, `core.event_occurrences` with `start_date` in [today, today + 12 months), or with no date and `make_date(year, expected_month, 1)` in that window: **407 occurrences, 256 with a confirmed date (63%), 151 `tbc` with an expected month, 0 with neither.** The serving view agrees: 413 occurrences, 260 dated. By month (dated / tbc):

```
2026-10   1 / 0     2027-04  39 / 13
2026-11  25 / 0     2027-05  29 / 15
2026-12  14 / 1     2027-06  25 / 13
2027-01  10 / 1     2027-07  23 / 9
2027-02   8 / 3     2027-08  12 / 15
2027-03  10 / 7     2027-09  38 / 36
                    2027-10  22 / 38
```

Nearly everything is dated through spring, about half from August 2027 on. Why the far months are `tbc` was not measured; organisers announcing late is a hunch.

**What does matter: the spec's `occurrence date >= today` drops every `tbc` row.** Of the 27 attendance rows on non-past occurrences today, 22 are dated and **5 are `tbc`**: Comrades Marathon 2027 (3 × interested, expected June) and athens half marathon 2027 (1 going, 1 interested, expected March). As written, the hub would not show those 5 marks. The view carries `occurrence_expected_month`, and the index already renders TBC tiles, so they could sit under their month as "date TBC".

The only other scraper lead: the 2026-10-30 entry on events with two editions a year (EcoTrail Paris). One occurrence per year means the hub would show one row where there are two. That is already an idea here, not a crew dependency.

### For Paulo to decide

1. **`private` vs. rule 2:** does the hub hide `private` members (keep today's promise) or show them to their crews (change settings, the privacy page, and tell the 3 affected users)?
2. **The existing roles:** keep `admin`/`member` (they gate invite rotation today, and "out of scope" can mean "build nothing more"), or remove them per the spec? Removing them means a migration and a new rule for who rotates the link.
3. **`tbc` editions on the hub:** under their expected month as "date TBC", or left off?
4. **Join:** keep today's confirm-then-POST, or join on GET as the spec says?
5. **Non-member:** keep `crews_hidden.html`, or 404 as the spec says?
6. **"My crews":** move it from `/settings` to `/profile`, or show it in both?

### Paulo decided, 2026-10-31 (his words, quoted; the notes under each are the analyst's)

1. *"Very good point. collapse to two level only."* Option (c): `private` goes, leaving `public` and `crews_only`. Rule 5 then holds as written. Follow-ons the web PM has to settle: a migration on `web.users.visibility` (today `String(16)`, default `public`, three values in the templates' radio); the settings, profile and privacy-page text; and what the 3 `private` users become. `crews_only` is the reading that keeps their current promise closest (hidden from strangers, visible to crew-mates), but it is a change for them either way and should be said to them before the hub ships. Nobody today is `crews_only`, so the migration touches 3 rows.
2. *"I just would like for members to be able to spread the link and to leave the crew if they want. The admin/creator is just one more member that is able to remove others, that's it."* So: keep `admin`/`member`; any member can share the link (true today, the URL is on the crew page for every member); any member can leave (step 6); **an admin can remove a member** — which is new, is the second half of the 2026-10-30 "leaving a crew, and removing someone from one" entry above, and is not in the spec's "In" list. The spec's "Out: roles, admins" is therefore narrowed to "no role management UI, no approval of members". Whether rotation stays admin-only was not asked; nothing said changes it. The 10-30 entry's open points (last admin leaves, admin removing an admin, rotating the link after a removal) still stand.
3. *"TBC still have a month and edition year. Go with a."* Shown under their expected month with a TBC date block.
4. *"go with a"* — keep the confirm step at `/crews/join/{token}`.
5. *"go with a"* — keep the hidden page for non-members.
6. *"with b"* — "My crews" moves to the profile page; the Settings crews block goes.

### Unexplained / not checked

- `crews_detail.html`, `ProfileService`'s timeline query and the W-072 diff were not read in full; the overlap claims are from function names and the commit message.
- The Claude Design canvas ("Crew hub sketches", artboard D) can't be read from here; the web PM gets the prose spec only.
- No query here measured how many rows a hub would show per crew today; at today's size it is small either way.

## Registration "closed" reads as misleading when the next edition's registration is still to open
2026-10-31 · ticketed W-088
*PM 2026-11-01: **ticketed W-088** (p3, after the crews arc). "Opens 3 Nov 2026" when the date is ahead; "Closed" when there is no date. 49 dated race rows, 17 events. Signed-in only: anon never sees registration status.*

Paulo: registration "closed" in the UI looks a bit misleading when the
registration for the edition is coming up. It should be rephrased.

Paulo, later the same day: it should actually say the actual date of the
registration, something like "opens on Nov 1st" instead of "coming up",
so long as the date exists.

## Show users as first name + last initial, not full name from Google
2026-11-01 · ticketed W-090 · **Paulo: highest priority, the most important thing at the moment**
*PM 2026-11-01: **ticketed W-090** (p1, `deploy: immediate`, the next ticket, ahead of the crews arc). Short form built at sign-in from `given_name` and `family_name`. Existing rows need migration 015, run by you after the code is serving: not every user signs in within 30 days, so the rest would keep their full name. Format taken as `Paulo M.`; veto at review.*

Paulo: at the moment we get the user name from Google, and that means
first name and last name. It is imperative we show first name and the
initial of the last name instead.

Where it comes from today: `app/services/user_service.py` stores Google's
`name` field as `display_name` on sign-in (and refreshes it on every
sign-in). Google also sends `given_name` / `family_name` separately, so
the initial can be built from those rather than split from the full name.

## Suggest a race: say "we get your race up and running in 24 hours or less"
2026-11-02 · ticketed W-097
*PM 2026-11-03: **ticketed W-097** (p3, after the crews arc). Default: the sentence goes in the banner paragraph, the button labels stay; veto at review.*

Paulo: add to the suggest-a-race text "we get your race up and running in
24 hours or less".

Where the text lives today: `app/templates/index.html` has two suggest
surfaces, the `suggest-btn` link near the top and the `suggest-banner`
block further down, both pointing at the Google Form.

## Event pages are the only place to mark a race; tiles lose the Going / Interested controls
2026-11-02 · ticketed W-096
*PM 2026-11-03: **ticketed W-096** (p3). Anon keeps "Sign in to join". Default: the read-only "You are going" line stays on a marked tile, since it is a status, not an option; veto at review.*

Paulo: event pages should be the only place where the user is able to
sign in to the race. Please remove the options from tiles. Tiles should
still keep the sign-up button when the user is not yet logged in.

Where it lives today: `app/templates/partials/race_tile.html`, hover
panel at the bottom. Anonymous users see "Sign in to join →" (keep).
Signed-in users see either Going / Interested buttons, or their current
status with Change / Remove (all of this goes). The event page keeps its
own controls.

## The profile's race list should use the crew hub's calendar format
2026-11-02 · ticketed W-098
*PM 2026-11-03: **ticketed W-098** (p3, M). Month headings, the hub's date block, distances, TBC under its month. Defaults: the Going / Interested / Been there flag stays, and Been there stays its own section; veto at review.*

Paulo: the crew hub has a race calendar format. This format should be the
same within the user's profile.


## scraper 2026-11-02 — suggested races that already exist: what people typed, and why search missed it
2026-11-02 · source: scraper analyst 2026-11-01 (Paulo's session, on his question about the Grossglockner suggestion), carried by the scraper PM at triage 2026-11-02 · A + B(i) ticketed W-099; C ticketed W-100; D, E raw
*PM 2026-11-03: **A + B(i) ticketed W-099** (p3): fold both sides in the web query and match the country column; no migration. **C ticketed W-100** (Paulo, 2026-11-03); it waits on the Form's prefill field id from him, **dropped 2026-11-05** on his word. **D, E and B(ii) left raw**, settled by Paulo picking them: B(ii) and E route to the scraper, D's log sink is already in infra's inbox.*

**Carrier's note (scraper PM).** Paulo's direction, in his words: *"let's include it in ideas. Because we have to make it easier for people to find"*. The options are the analyst's, unranked, and Paulo decides which and in what order. Search lives in your `race_service.py`, so **A, B(i), C and D's in-app variant are yours.** Two options would land in the scraper repo if you ask for them: **B(ii)**, a folded `search_text` column on the serving view, or `unaccent`/`pg_trgm` installed by a migration; and **E**, stored aliases per event, new `core.*` data that needs a source. Neither is ticketed there; ask through the scraper's `docs/IDEAS.md`. **D's log-sink variant** was carried to `indie-runners-infra`'s inbox the same day, as an alternative to your in-app recording; C makes D permanent by itself. The client IPs the analyst used to group sessions stay out of every file. Verbatim from the scraper's `docs/IDEAS.md`:


Paulo asked: *"some people are suggesting races that already exist, I am wondering what keyword combination they were using to not be able to find the race … Is there a way to get that check? Grossglockner was one of those races"*

Paulo, on reading the answer: *"let's include it in ideas. Because we have to make it easier for people to find"* — the direction is his; the options below are the analyst's.

**Yes, there is a check: the web service's Cloud Run request logs (verified).** The search box is
a plain GET form (`/?search=<term>`), so every query lands in the request
log with its full URL. Suggestions themselves go to a Google Form
(`forms.gle/TSE2…`), which records nothing about the search. GoatCounter is
aggregate only. Rerun:

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="indie-runners-web" AND httpRequest.requestUrl:"search="' \
  --project indie-runners-dev-470411 --freshness=30d --limit=5000 \
  --format='value(timestamp,httpRequest.requestUrl)'
```

Then decode `search=` and replay each distinct term against
`core.v_denormalized_event_data_upcoming` with the web's own rule:
`ILIKE '%term%'` on `event_display_name`, `event_name`, `race_location`,
`terrain_type`, inside its upcoming window (`race_date >= yesterday`, or
`tbc` with expected month ≥ this month). Grouping one visitor's session needs
the client IP, which is personal data: query it ad hoc, never write it down.
**Retention is 30 days** (`_Default` bucket), so this check only looks back a month.

**Grossglockner (verified, same day).** One visitor tried eleven searches
(`Großglockner`, `Ggut`, `Ultratrail` and variants) before giving up. The
catalogue holds event 44850 as `Grossglockner Ultra Trail` /
`Grossglockner Ultra-Trail` (2027-07-22, in the window). Every one of those
terms returns 0 for it:
- `Großglockner`: ß ≠ ss, and ILIKE does not fold them.
- `Ggut`: the acronym appears nowhere in the row.
- `Ultratrail`: matches 4 other events, but not "Ultra Trail" or "Ultra-Trail".

Searching `gross` or `glockner` finds it.

**Across all searches (per-term hits verified, classification believed).**
2026-10-13 → 11-01. Two probe/injection rows
(a WordPress REST probe, a template-injection attempt) were excluded, leaving 75
distinct terms, 18 of which return 0 against today's view:

| Why it missed | Terms | What the catalogue has |
|---|---|---|
| Diacritic / transliteration | `Großglockner`, `Fränkische`, `Kiev`, `Transilvania`, `Julien`, `Julien Alps`, `JulienAlps` | Grossglockner Ultra Trail, Lowa Ultratrail **Fraenkische**, **Kyiv** Marathon/Half, **Transylvania**, **Julian** Alps Trail |
| Spacing / punctuation | `Valdaran` (also `JulienAlps`) | **Val Daran** Pyrenees |
| Country typed into search | `Malta` | Gozo Trail Run, Valletta Marathon, both `event_country_code = 'malta'`, a column search does not look at |
| Acronym | `Ggut`, `UTFS` (hunch: Ultratrail Fränkische Schweiz) | no alias stored anywhere |
| Not in the catalogue | `Florence`, `Kullamannen`, `Halloween`, `ironman`, `impact marathon`, `Trans dimitile`/`Transdimitile` (Réunion, outside Europe) | — |

So **about 11 of the 18 failed searches were for races we already
have**. Fixing diacritics and spacing alone would catch 8 of those 11.
Context: of the 409 events in the window, 17 have "ss" in a name and 24 have a diacritic.

**Options (Paulo decides whether and in what order; the PM routes them):**
- **A. Search the country column too.** One more `ILIKE` on
  `event_country_code`. That fixes `Malta`: a country name typed into the box. Web.
- **B. Fold both sides before comparing.** That means lowercasing,
  ß→ss, ä/ö/ü→ae/oe/ue *and* a/o/u, stripped accents, and removed spaces and hyphens.
  Neither `unaccent` nor `pg_trgm` is installed (`pg_extension` lists only
  `plpgsql`, `uuid-ossp`), so either:
  (i) `translate()`/`replace()` in the web query (web), or
  (ii) a folded `search_text` column in the view (this repo, `core.*`).
  Installing `unaccent`/`pg_trgm` would be a migration here, and `pg_trgm`
  would also catch typos like `Julien`→`Julian` and `Transilvania`.
- **C. A zero-result state that offers the suggest form, pre-filled with the typed
  term** (Google Forms pre-fill URL). The form then records the failed query
  next to the suggestion, and the check becomes permanent and exact. Web.
- **D. Keep the evidence past 30 days**: a log sink for `?search=` requests
  (infra), or the web app recording zero-result searches itself (web).
- **E. Aliases** (`GGUT`, `UTFS`, `Kiev`): a stored short name or alias per
  event. That is new `core.*` data (this repo). It needs a source, and it is the biggest of the five.

**To confirm from the producing side:** the Form's response timestamps.
A Grossglockner suggestion on 11-01 would tie it to the session above.
Without that, the link from that session to the suggestion is believed, not verified.

**Unexplained:**
- The replay runs against today's view, not the view at search time. A
  term that hits today (e.g. `glockner`) may have missed on 10-22, and a
  race added since would read as "found".
- Visitor counts are approximate. `Julien Alps` came from four addresses
  within one second (17:48:53Z on 10-20), and `Julien`/`JulienAlps` did the same
  on 10-31. That looks like a link preview or a rotating IPv6 prefix, not four people.
- The oldest web-service log entry reads 2026-06-15, against a 30-day
  bucket retention. I did not chase this.

## Remove the small-crew anonymity hint from the crew page
2026-11-02 · ticketed W-095
*PM 2026-11-03: **ticketed W-095** with the filter entry below (p2, crews arc, `deploy: immediate`). Both are deletions on the same page.*

Paulo: "Small crews may reveal who is going — larger crews give more
anonymity." Remove that please.

Where it lives: `app/templates/crews_detail.html`, shown under 4
members. `docs/ARCHITECTURE.md` (small-crew leak) explains why it was
added and already allows for removing it.

## Drop the "Going and interested" / "Going only" filter on the crew hub
2026-11-02 · ticketed W-095
*PM 2026-11-03: **ticketed W-095**, with the hint entry above.*

Paulo: Going and interested / Going only filter button on crew hub, that
can go.

Where it lives: `app/templates/crews_detail.html`, the "Agenda filter"
group of two links, backed by `?view=going` on the crew route.

## One bash script for a whole Unsplash round
2026-11-03 · raw
*PM 2026-11-04: **ticketed W-104** (p4, tooling). The restart reloads the tiles but not the credits: startup skips a slug its baked manifest lacks, so the backfill is the step that sets them. Choosing the round's events stays by hand.*

Paulo: include a script to do this in one whole bash script.

Today a round is five manual steps after picking:
`scripts/unsplash_fetch.py` per event with `--no-publish`, then
`generate_dedicated_manifest.py`, `python -m app.imaging --style
passthrough --tile-version v02`, a Cloud Run restart (redeploy the
serving image by digest), and `backfill_event_image_attribution.py`.
The last step is easy to miss: a restart alone leaves the new photos
under the old stock credits, because the credit comes from the manifest
baked into the running image (seen 2026-11-01). Choosing which events
and queries go into a round is also done by hand each time.

## scraper 2026-11-03 — a registration start on or after the race date is no longer stored (0.89.0)
2026-11-03 · raw · source: scraper T-197
*PM 2026-11-04: **W-088 amended**, no new ticket. Its acceptance 4 stays as a guard for rows not yet re-run; both paths read "Closed".*

For your W-088 ("Closed" when the start is on or after the race). The scraper shipped 0.89.0 on 2026-11-03 ~11:16Z.

**The scraper's 2026-11-01 web-audit entry read `registration_start >= race_date` as "the next edition's date on this edition's row". For the UTMB cohort that reading is wrong.** On every UTMB World Series homepage each race card shows a status badge followed by the race date, and flattened to text they run together: `Registrations open17th June 2027ZUT100`. The model stored the race's own date as the registration start. On 2026-11-03, 130 of the 737 upcoming rows with both dates had start >= race (76 equal, 54 after). 35 were UTMB card badges on 10 events, 16 were race-day check-in, bib pick-up or on-site registration, and most of the 53 other "after" rows are the next edition's opening filed on this edition's row (Amsterdam "Registration starts December 19th", Stockholm, Leipzig). That last group is the reading the audit entry had.

**What the scraper now refuses:** a `registration_start` on or after the same race's `race_date` for the same edition is stored as null. That applies to a new answer, and to a stored value when a later run finds nothing. `registration_start` also carries instructions now: a status label followed by a date is not an opening date, and bib pick-up, check-in and on-site or late registration are not opening dates. The rule is `>=`.

**What you will see:** those rows move from a date to null as each target is next re-run (registration refresh, 3 to 7 days), so W-088 renders them by its no-date branch, not as "Closed" from a race-day start. Zugspitz is already done: a hand run at 11:18Z left all 7 races with a null start, no 2027 date. A nulled value is not destroyed. It moves to the scraper's answer history, where its T-131 picks up the next-edition openings.

**Not changed:** `registration_open = true` with a start still ahead (66 rows) and sold out with a start still ahead (10 rows) stay raw in the scraper's IDEAS. Pre-registration and priority windows make some of them real.

## "← All events" on an event page drops the filters the user had set
2026-11-04 · raw
*PM 2026-11-04: **ticketed W-102** (p3). Answer to Paulo's question: no, the link should return to the filtered list, and `/` when there was no filter. Scroll position out.*

Paulo: once the user uses the filter, checks one race, and decides to
come back, clicking "← All events" shows all the tiles again. Is this
correct, or should people be expected to hit the browser's back button
to get their filters back?

Where it lives: the link in `app/templates/event.html` is a hard
`href="/"`. The index filters are query parameters (country, search,
terrain...), so the filtered list already has its own URL; the link just
doesn't carry it.

Good practice, from the developer session that filed this: a "back to
results" link should return to the results the user left, filters and
scroll position included. Relying on the browser's back button is not
enough: people arriving from a shared link or a new tab have no history,
many mobile users never use it, and a link labelled as a way back that
silently resets their search reads as a bug. The usual fix is small:
carry the list URL into the event link (or use the referrer when it is
our own index) so "← All events" goes back to the filtered view, and
keep "All events" as plain `/` only when there was no filter.

## Crews arc, highest priority: profile empty states, and two tickets moved up
2026-11-04 · raw · **Paulo: highest priority, part of the crews arc**
*PM 2026-11-04: items 1 and 2 **ticketed W-101** (p2, `deploy: immediate`, the next ticket). Default: the jump lands higher, the button stays; veto at review. Items 3 and 4: **W-096 and W-098 raised** to p2, `deploy: immediate`. `docs/PLAN.md` steps 8 to 10.*

Paulo, four things for the PM to triage together:

1. **Crews link lands below "Create a crew" on mobile.** Clicking Crews
   in the profile drop-down opens the profile; on mobile it jumps
   straight to the My crews section. A first-time user sees "You're not
   in any crews yet. Create one, or ask a friend for an invite link."
   and has to scroll up to find "Create a crew". Either the jump should
   land a bit higher, so the button is visible, or the button should
   move under the box, and so under the list of crews joined or created.
2. **"No races on your calendar yet" should sit in a box**, like the
   "You're not in any crews yet" message.
3. **W-096 (tiles lose the Going / Interested controls) goes up in
   priority.**
4. **W-098 (profile race list in the crew hub's calendar format) goes up
   in priority.** The hub's calendar is great; the profile just needs the
   same.

Developer notes, for item 1 and 2 (not checked in a browser):
`app/templates/profile.html` puts "Create a crew" in the section head
next to the "My crews" title, and the link targets `#crews`, the section
itself. So the button should already be at the top of the jump; that it
isn't suggests the sticky nav covers the section head. If so,
`scroll-margin-top` on the section is the one-line fix for the first
option. The calendar's empty text is a bare `<p class="profile-empty">`;
the crews one uses a `crews-empty` box.

## Header wordmark: the dot on the "i" of "Indie" in amber, like the ir logo
2026-11-04 · raw · **Paulo: up in priority**
*PM 2026-11-04: **ticketed W-103** (p3), first after the crews arc. Default option 1; veto at review.*

Paulo: the letter i in the header logo should have its dot in the yellow
colour, just like the logo in `static/brand/`.

Developer notes (not tried in a browser). The header wordmark is live
text, "Indie Runners" in Fraunces Bold, white, in `base.html` /
`.logo-name` in `main.css`. The only lowercase i is the one in "Indie".
The brand amber is #e8a44a (`--accent`). The ir mark is cut from the
same font, so the match should hold. Three ways, smallest first:

1. **Colour the top of that one letter.** Wrap the "i" in a span and
   give it a two-stop text gradient (amber above the stem, white below)
   with `background-clip: text`. The page text stays "Indie Runners" for
   search, copy-paste and screen readers. The cut-off sits in em, so it
   scales with the font, but needs tuning once by eye.
2. **Dotless ı plus a drawn dot.** Swap in U+0131 and put an amber circle
   above it with a pseudo-element. Exact control over the dot, but the
   text becomes "Indıe" unless the link carries an aria-label.
3. **An SVG wordmark** built the way `build_assets.py` builds the ir
   mark, from Fraunces outlines. Pixel-exact to the brand, but a new asset
   to maintain, and the tagline stays text beside it.

Option 1 is the likely pick. The 2026-10-21 entry left "where the main
logo goes" raw; this is an answer for the header.

## Tile hover panel: the buttons at the bottom get hidden on crowded tiles
2026-11-04 · raw · **Paulo**
*PM 2026-11-04: **ticketed W-107** (p2, `deploy: immediate`), next after W-098 closes the crews arc. The tile is a fixed 3:4 that hides overflow, and the panel has no height limit. Default: pin the last line, and a "+N" pill for distances that don't fit; veto at review.*

Paulo: the biggest problem with the tiles nowadays is that, where there
are many races per event, or many people going/interested, then the
buttons get hidden in the bottom, both on desktop and mobile.

Developer note (read from `race_tile.html`, not seen in a browser): W-096
removes the Going / Interested / Change / Remove buttons, which are the
last things in the panel, so for a signed-in runner only the one-line
status stays down there. The signed-out "Sign in to join →" sits in the
same last slot and still falls out of view after W-096. That is the hover
panel's layout, not the buttons; likely its own ticket after W-096.

## GPX files on the event page: what the scraper knows today, and what it does not
2026-11-06 · raw (web triage 2026-11-10: left raw; settled by Paulo's hosting-vs-linking ruling on the scraper side, then render-vs-link and per-race-vs-per-event; the only candidate next arc on the table, so Paulo's to pick) · source: scraper PM triage 2026-11-06, carrying Paulo's idea of 2026-11-05 from `indie-runners-scraper`'s `docs/IDEAS.md`, "of high priority"

Paulo: *"of high priority, start exploring ideas as to how to extract the gpx file automatically, and then how to use it on the web interface. I am thinking, having a sole repository which has all gpx files for all events and races. A script that renders the file into image tiles and connects them to their respective events/races/editions. Another script analyzes scraped content and determines whether the gpx file could be extracted automatically at scraping time or also as a manual process."*

**This is the interface half, and it cannot be built yet.** The scraper side is a raw arc in that repo's `docs/PLAN.md`, with no ticket, because no repository of files exists. Nothing here is asked of web now except a view on what the page would want, which shapes what the scraper has to keep.

**What exists today, measured on `answers.tier_answers`, 2026-11-06:** `gpx_available` is `true` on 732 rows across 174 events, `false` on 488 across 196, null on 1,512 across 342. Only 33 of the `true` rows have a URL in their quote. Examples of the quotes: `GPX Daten BaseTrailPfalzTrail - BaseTrail.gpxXML Dokument109.2 KBDownload` (`engelhorn_sports_pfalztrail`), `Download file:bergmarathon_ebensee_gmunden-1.gpx` (`sport_traunsee_bergmarathon`). So core can say a file exists and usually cannot say where. The answer is not proven accurate: accuracy round 2 marked `tilburg_ten_miles`' `false` as `wrong`.

**Questions for the web side:**

1. A rendered map, a profile, a download, or a link to the organiser? Paulo's idea names image tiles. The scraper needs to know which, because a link needs a URL, and a render needs the file.
2. Per race or per event? A race usually has its own course, and one event carries several.
3. Paulo has been asked on the scraper side whether re-serving organisers' files is acceptable at all, as against linking to them. Hold design on hosting until he rules.

## A skill that starts an Unsplash photo round
2026-11-06 · ticketed W-115 (Paulo chose A, 2026-11-10; after W-104) · source: scraper analyst 2026-11-06 (Paulo's session), written on his behalf in that repo's `docs/IDEAS.md`, carried by the scraper PM at triage 2026-11-06. The decisions quoted are his, everything else is the analyst's. A, B or C is for this repo to take to him


Paulo: *"create a skill to start the process of selecting photos in unsplash, seemlessly."*

**Not a duplicate of W-104 (verified).** W-104 (open, p4, no script yet) covers the five steps after the pick, and its spec puts "Choosing which events and queries go into a round" out of scope. This idea is that earlier part, so the two meet at W-104's input file of `<slug> [query]` lines. Web's 2026-11-03 entry names the same gap: "Choosing which events and queries go into a round is also done by hand each time."

**Why it matters now (verified).** Six commits from 2026-11-01 to 11-04 added 10, 14, 17, 12, 14 and 15 events, 82 in all, each a round by its commit message. The start of a round today is `scripts/photo_candidates.py` for the ranking, a query chosen per event, then `scripts/unsplash_fetch.py <slug> --no-publish` once per event. `docs/IMAGING.md`, "Sourcing photos from the Unsplash API", is the procedure.

**The constraint that shapes it (verified).** The pick in `unsplash_fetch.py` is `input()`, and `prompt()` turns `EOFError` into `s`. `input()` raised `EOFError` under Claude Code's Bash tool in this session. So a skill calling the script as it stands would print "no input available, skipping" for every event and exit 0, having spent the search request and written nothing.

**Options for the pick, the analyst's:**

| Option | How the pick happens | What it changes | Seamless? |
|---|---|---|---|
| A. Skill prepares, Paulo picks in his terminal | The skill runs the shortlist, agrees the queries in chat and writes the `<slug> [query]` file. Paulo then runs the round in a terminal, as he does today | The skill only | Up to the pick, then a change of window |
| B. Pick in chat | The skill gets the candidates, Paulo opens the contact sheet and names a photo in chat, and the script fetches that photo with no prompt | A new non-interactive flag on `unsplash_fetch.py`, which W-104 says not to change, so a ticket or an amendment | Yes, but the most work |
| C. Fold into W-104 | As A, with the shortlist step added to W-104's script instead of a skill | W-104's scope; the "skill" Paulo asked for becomes a bash command | Same as A, with no agent to help on queries |

- **The analyst's recommendation, believed:** A first. It needs no script change and the file it writes is W-104's input. B is worth a ticket if the window change is still the friction. If B is built, the flag should name a photo id rather than a list position, because a second search may not return the same order (hunch).
- **What a skill cannot remove (verified from `docs/IMAGING.md` and the script's docstring).** The photo choice stays by eye. Trail events need `--query` "almost every time", because the tile location is a village nobody photographs, so a skill can propose a query but Paulo still judges it.
- **Limits it must respect (verified from the code and `docs/IMAGING.md`).** The demo tier is 50 requests an hour, about 25 events, and each "m for more" costs another search. Both scripts open the database, so the one-session rule across both repos applies to the whole round.
- **Whose it is (verified).** Web's `docs/roles/README.md` gives `.claude/skills/` to its chief of staff. Web has only role skills (`audit`, `cos`, `dev-ticket`, `review`, `triage`), so this would be its first command of Paulo's own, the shape of `/trust` and `/lane` here.

**Not checked.** How many stock events are left to convert (not queried, `photo_candidates.py` reports it). Whether `webbrowser.open` fires from a skill-driven run. Whether Claude Code's `!` prefix gives the script a usable stdin; if it does, A's change of window goes away.

**For Paulo to decide:** A, B or C. It decides whether W-104's "don't change the scripts" holds. No skill was created by this entry.

## Lock the Python dependencies, highest priority
2026-11-09 · ticketed W-112 (triage 2026-11-09: p2, after W-111) · source: Paulo, after the 2026-11-09 public-release audit

Paulo: *"please draft it in ideas, as highest prio at the moment"*

**What is wrong (verified).** `requirements.txt` pins only SQLAlchemy (`>=2.0.0,<2.1`); every other package is a floor (`fastapi>=0.111.0` and so on). Its own comment says pinning the rest "is a separate change", which never happened. The Dockerfile runs `pip install -r requirements.txt`, so each `scripts/deploy.sh` build takes whatever is newest that day.

**Why it matters here.** There is no test suite, so a dependency that changes behaviour (FastAPI, Starlette, pydantic) is caught only by the manual run before deploy, or not at all on a route nobody clicked. The same commit built twice can give two different images, so a regression cannot be split into "our change" and "a dependency moved". Unpinned requirements on a production service are also among the first things a reader checks once the repo is public.

**A starting shape, not a spec.** Keep `requirements.txt` as the direct dependencies. Generate a fully pinned file from the image now live (`pip freeze` inside it), so the pins equal what production already runs. The Dockerfile installs from the pinned file. Upgrades become a deliberate change. Once public, Dependabot (free) raises security bumps against the pins. Hashes (`--require-hashes`) are optional.

**Not a blocker for the move to the public repo.** A good first change after the flip.

## Search Console: why pages aren't indexed
2026-11-11 · source: Paulo, pasted from Google Search Console's page indexing report

```
info_filled
Why pages aren’t indexed
Pages that aren’t indexed can’t be served on Google
Reason
    Source

    Validation
    Trend    
Pages
Not found (404)
    Website
    
Not Started
    
    6
Excluded by ‘noindex’ tag
    Website
    
Not Started
    
    3
Page with redirect
    Website
    
Not Started
    
    3
Duplicate without user-selected canonical
    Website
    
Not Started
    
    2
Blocked due to other 4xx issue
    Website
    
Not Started
    
    1
Crawled - currently not indexed
    Google systems
    
N/A
    
    0
Rows per page:
1-6 of 6
```
