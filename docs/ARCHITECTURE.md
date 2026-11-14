# Architecture

## Overview

Indie Runners Web is a standalone FastAPI service that serves server-rendered HTML. Users authenticate with Google OAuth, browse European races, and mark attendance. It shares a Cloud SQL PostgreSQL instance with two other services but owns its own schema.

## Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| Templating | Jinja2 |
| ORM | SQLAlchemy 2.x (sync) |
| Database driver | psycopg 3 |
| Config | pydantic-settings |
| Runtime | Cloud Run |

## Database

The service shares a PostgreSQL instance with `indie-runners-scraper` and `indie-runners-bot`.

| Schema | Owner | Access |
|---|---|---|
| `core` | indie-runners-scraper | Read only |
| `web` | this service | Read and write |

SQLAlchemy `Base` is declared with `MetaData(schema="web")` so all models land in the `web` schema by default. Queries against `core.*` tables use explicit schema overrides.

## The core read model

Everything this service reads from `core` comes through one mapped object:
`Race` in `app/models/core.py`, pointed at `core.v_denormalized_event_data_upcoming`.
That view is owned by indie-runners-scraper and wraps
`core.mv_denormalized_event_data`, filtering it to rows that belong to the
current occurrence so stale prior-edition races cannot attach to a fresh one.
The file carries a READ ONLY banner: this service never writes to `core.*`, and
schema changes there arrive from the other repo's migrations, not this one's.

**The grain is one row per race, not per event** — every tile and every
event page groups N rows down to one, and that regrouping is where most of the
subtlety in `RaceService` lives. Each event has exactly one live occurrence, so
the grouping key is the event and nothing needs to disambiguate editions.

*Measured 2026-08-28: 1724 rows across 356 events, 1 to 18 races per event,
averaging 4.8. Counts of the view, anywhere in this document, are measurements with a shelf life — they
are dated for that reason, and the conclusions drawn from them are written to
stand without them.*

**Declarations checked against the view on 2026-10-25 (W-014).** One
`information_schema.columns` query: 54 of the 55 mapped types matched, and
`occurrence_id` (`text`, which had been declared `Integer`) was fixed. Nullability can't be
checked this way, because Postgres reports every view column as nullable. The view has 102
columns and the model maps 55. A scraper migration that touches the view makes
this date stale.

Which fields are safe to read off a single row depends on their grain, and this
is verified against production rather than assumed:

| Grain | Fields | How to read |
|---|---|---|
| Event-level | `event_display_name`, `event_slug`, `event_country_code`, `event_website_url`, `event_type`, `short_description`, `occurrence_*` | Identical on every row of the event; read off any row |
| Race-level | `race_distance`, `cumulative_ascent`, `cutoff_time`, `terrain_type`, `race_format`, `registration_*`, `start_time`, `race_date`, `race_location` | Varies within an event; must be aggregated or the row must be chosen deliberately |

The event-level row of that table is a claim that has to be re-earned as the
corpus grows, and it was: re-checked 2026-08-28, **no event carries more than
one distinct value** in any of those columns, and none mixes a populated value
on one race with a NULL on another. `short_description` is the one that matters
most — `RaceService` reads it off a single row — and it holds on both tests.

**An event's location is one rule, `event_location()` in `race_service.py` (W-070,
1.9.46): the event's `event_location` (its HQ), else the first race in first-see
order — `race_date`, then `mv_id` — that has a `race_location`, else nothing.**
The tile, the event hero, both calendar links and the profile calendar call it;
no page keeps its own read. `event_location` is NULL on every row (0 of 396
events, measured 2026-10-30; 0 of 1724 rows on 2026-08-28) until the scraper
populates it (their T-039), so today every page shows a race start town, and the
day the HQ lands it takes over with no web change. `race_location` is
*race*-grained: 90 events carried more than one value on 2026-08-28, and on
2026-10-30 four events (`biegi_gorskie_sanok`, `kielder_marathon`,
`otf_presented_by`, `walt_disney_world`) had no town on their first-see row but
one on a sibling, and ten had no town on any race — those show "—" on the tile
and no location item in the hero. The function sorts the rows it is given, so
the hero's distance-ordered rows and the tile's date-ordered rows agree. Before
W-070 the tile took the first-see row's value NULL or not, the hero read the dead
column, and the profile skipped NULLs in SQL — when that choice was reimplemented
in SQL it once diverged on 11 events (on or before 2026-08-10) because ties on
the coalesced sort key resolve differently in Postgres than in Python; **since
1.9.34 (W-029) `mv_id` breaks ties**, so for the same surviving rows the first
one seen no longer depends on the query plan. A filter that drops some of an
event's races (dates, or `search` on location/terrain) still changes it.

The race-level fields genuinely disagree in practice — 278 events carry more
than one distance, 105 more than one cutoff, 56 more than one terrain (measured
2026-08-28). Reading such a field off `rows[0]` is a bug, and has been one
three times: the event page's hero-image call once passed `first.terrain_type` when a
sibling race held the real value, the format filter once collected only on
first-see and missed events whose earliest-dated race had no format, and the
tile price was one race's value rendered with a `+` as if it were the floor.
Price is now a range over every priced race (`price` the floor, `price_max` set
only when races differ; under mixed currency `price` is the earliest-dated
positive price, not a floor, and there is no range); NULL price, and a positive price with NULL currency,
are unknown and excluded, never free.

Type quirks worth knowing before writing a query against it:

- **`race_format` is a JSON array serialised to text** — `'["relay", "timed"]'`,
  never a bare scalar. A race can hold several formats. Not queryable in SQL as a
  relation; parse with `parse_race_formats`.
- **`occurrence_year` and `occurrence_expected_month` are text**, matching the
  MV's habit of projecting everything as text. Cast to `Integer` at query time
  wherever they feed `make_date` / `COALESCE` arithmetic.
- **`cutoff_time` is hours as a float**, and the source data includes physically
  impossible values (a 1-hour marathon, a 45-hour half). Tickets A and B.
- **`mv_id` is `uuid`, and is mapped as one** — `Uuid(as_uuid=False)`, which
  keeps the Python-side value a `str`. It was mapped as `Text` until W-007
  (2026-08-28), which made any load-by-primary-key emit
  `WHERE mv_id = $1::VARCHAR` and raise
  `operator does not exist: uuid = character varying`. That fired whenever a
  `Race` was expired and re-accessed — in practice, whenever anything committed
  on the request's session mid-render. The lesson is worth more than the fix:
  it was diagnosed in 1.6.0 (2026-08-10), routed around, and still armed
  eighteen days later, because a workaround reads like a closed defect.
- **Coverage is uneven and consuming surfaces must degrade** rather than render
  an empty affordance. Measured 2026-08-28: `short_description` on 353 of 356
  events, `race_format` on 90, `cutoff_time` on 149. The shape of that claim —
  descriptions near-universal, the other two partial — is what the surfaces are
  built against; the figures move, and `cutoff_time` in particular is climbing.

## Tables owned by this service

**web.users**
- `id`, `email`, `display_name`, `avatar_url`, `created_at`, `updated_at`
- `display_name` holds the short form **`Paulo M.`** (given name, last initial, period), written by `short_display_name` in `user_service.py` on every sign-in: given name + family initial when Google sends both, else the first and last tokens of `given_name`, else of `name`, NULL when Google sends nothing (W-090, W-091). Migration 015 backfilled rows written before 1.9.56; Paulo ran it 2026-11-01. Every surface renders the column verbatim; nothing splits or re-derives it.
- `visibility VARCHAR(16) NOT NULL DEFAULT 'public'` with `CHECK visibility IN ('public','crews_only')` (`users_visibility_check`) — added as a tri-state in migration 009; migration 014 (W-076) moves the `private` rows to `crews_only` and narrows the CHECK, because a crew must always see its members' attendance (Crews v1 rule 2). The settings form offers the two, labelled **All indie runners** / **Crews only**; `public` survives only as the stored value. Until 014 runs, a `private` row is still hidden by the predicates' fallback.
- `strava_athlete_id`, `firstname`, `lastname`, `profile_photo_url` — kept temporarily, dropped in migration 004

**web.crews**
- `id`, `slug UNIQUE`, `display_name`, `created_at`, `created_by`
- `created_by` is a soft reference to `web.users.id` (no FK — orphaned-crew handling on user delete is deferred).
- Added in migration 010.

**web.crew_memberships**
- `crew_id` FK cascade → `web.crews.id`, `user_id` FK cascade → `web.users.id`, `role VARCHAR(16)` `CHECK role IN ('admin','member')` DEFAULT `'member'`, `joined_at`
- Composite PK `(crew_id, user_id)`. `idx_crew_memberships_user` supports the per-request viewer-crews lookup.
- Added in migration 011.

**web.crew_invites**
- `id`, `crew_id` FK cascade → `web.crews.id`, `token VARCHAR(64) UNIQUE`, `created_by`, `created_at`, `revoked_at`
- `token` is a `secrets.token_urlsafe(32)` value. Active-vs-revoked is `revoked_at IS NULL`; rotation is one UPDATE (set `revoked_at`) plus one INSERT (fresh token).
- Added in migration 012.

**web.auth_identities**
- `id`, `user_id`, `provider`, `provider_user_id`, `provider_email`, `created_at`, `last_used_at`
- One row per login method per user. `provider = 'google'` for this release.
- UNIQUE `(provider, provider_user_id)` and `(user_id, provider)`

**web.attendance**
- `id`, `user_id`, `event_id`, `occurrence_id`, `status` (`going` | `interested`), `created_at`
- `race_date DATE` — snapshot of `core.event_occurrences.start_date` at mark time; used to split Going vs Past on the profile without hitting the MV (since W-098 the profile reads `COALESCE(race_date, o.start_date)`, so a snapshot taken while the date was unknown picks up the date the edition has since gained; dated snapshots are read as taken). **May be NULL** when the user marks attendance on a TBC occurrence (the source `start_date` is NULL by definition until the organiser publishes the date). `ProfileService.is_upcoming` treats NULL as forward-looking, so TBC RSVPs land in `going_upcoming` / `interested`, not `going_past`. `occurrence_id` is stable across the backend's in-place TBC → upcoming flip, so the RSVP survives — the snapshot is only rewritten if the user re-marks after confirmation.
- `event_display_name VARCHAR(255)` — snapshot of the event name at mark time; fallback if the event is later removed from `core`.
- Attendance is edition-level: one row per user per occurrence. UNIQUE `(user_id, occurrence_id)`.
- `event_id` is a soft foreign key to `core.events.id`; `occurrence_id` is a soft foreign key to `core.event_occurrences.id` (no DB constraints — `core` is owned by another service).
- Mark and delete share one guard, `is_locked` (W-072): an occurrence is locked the day after its last known day (`core.event_occurrences.end_date`, else `start_date`), read live, not from the `race_date` snapshot. A locked occurrence answers 400 to both routes and the event page offers no control (a tile offers none at all since W-096: the event page is the only place to mark a race), so past history is preserved and cannot be written after the fact. NULL dates (TBC) never lock.

**web.event_images**
- `id`, `event_id` UNIQUE, `event_slug`, `created_at`, `updated_at`
- One row per event, holding the tile/hero image assignment. `event_id` is a soft reference to `core.events.id` (no FK — `core` is owned by another service); `event_slug` is indexed because the dedicated-photo path and `refresh_dedicated_attributions` both look up by slug.
- `kind VARCHAR(20) NOT NULL DEFAULT 'stock'` with `CHECK kind IN ('dedicated','stock')`, plus `CHECK (kind = 'dedicated' OR stock_filename IS NOT NULL)` so a stock row can never exist without a file.
- `stock_filename` — the chosen file from `app/imaging/stock_manifest.json`. Ignored entirely for dedicated events: `resolve_tile_image` serves those from `dedicated/{event_slug}.webp` based on the startup slug cache, not on this column.
- `terrain VARCHAR(20)` — the bucket the stock file was picked from. **Not a copy of the source `terrain_type`**: `_normalize_terrain` maps NULL and `other` to `mixed`, so a stored `mixed` may mean "genuinely mixed", "other", or "source was NULL when this row was inserted". That ambiguity is what `_heal_defaulted_terrain` exploits — see the Static assets section.
- `attribution_name`, `attribution_url`, `attribution_source_url` — photographer credit, added in migration 013. All three nullable; the hero template degrades from the full two-link Unsplash form to plain `Photo · {name}` to nothing. These must always be rewritten together with `stock_filename`, or the page credits the wrong photographer.
- `source` and `attribution` are **dead columns** from migration 007, superseded by the three `attribution_*` columns above. Still mapped in `app/models/web.py` but written by nothing and populated in 0 of 238 rows. Dropping them needs a destructive migration, so they stay until there is a reason to run one.
- Rows are inserted lazily on first render via `on_conflict_do_nothing`, so the insert is a race-safe no-op when two requests hit a new event simultaneously.

## Signed-out UX and per-user visibility

Anonymous visitors always see real per-attendee counts on the index tiles, but never real avatars, names, or profile links — the identity strip renders neutral silhouette placeholders instead. On the event detail page the action bar carries no counts (removed in 1.5.1, because ~92% of events had zero RSVPs and the number duplicated the section below); attendance is conveyed there by the Who's coming section, whose silhouettes and `+N` overflow chip are still driven by the real counts. Counts are always computed and never suppressed for privacy — where a surface shows a count, it is the true one. That is the fixed floor of the privacy model; which surfaces choose to display a number is a presentation decision, not a privacy one.

Signed-in visibility is governed by each attendee's own `web.users.visibility` (added in migration 009): `public` identities are shown to any signed-in viewer, and `crews_only` identities are visible iff the viewer shares at least one crew with the attendee; any other value (a `private` row before migration 014) is hidden from everyone but the attendee themself. Counts always contribute regardless of level. The rule is applied at read time in `AttendanceService.get_attendance_summary`, which takes `viewer_user_id: int | None` and `viewer_crews: set[int] | None` and filters both `going_users` and `interested_users` — the going and interested strips are governed by one lever, not two. Retroactive hiding is free because visibility is a property of the viewer×attendee pair, evaluated on every request.

The `crews_only` branch of the filter costs at most one extra bulk query per summary call: routes resolve `viewer_crews` once via `CrewService.get_viewer_crew_ids`, and the summary loop resolves attendee crew sets in one `CrewService.get_attendee_crew_ids` call scoped to the `crews_only` attendees present in the current summary. That second query is skipped when the viewer has zero crews or when no `crews_only` attendee is present. Two queries max per summary call regardless of N attendees.

`AttendanceSummary` also carries `going_hidden_count` and `interested_hidden_count` — the number of attendees who contribute to the count but whose identity was filtered. The shared `partials/avatar_strip.html` macro uses these to render stock silhouettes in the slots hidden attendees would have taken (up to the strip cap), then an overflow chip for anything past the cap. This collapses the anon-vs-signed-in template paths into one call: for signed-out viewers every attendee is hidden and the strip is entirely silhouettes; for a mix of public and crews-only attendees the strip shows real avatars first, then silhouettes, then `+N`. The same anonymous avatar (`anon_avatar` macro, `.avatar--anon-N`: a runner glyph on one of five backgrounds) is used for every privacy tier across the site — index tiles (their front face; the hover panel shows counts only, W-107), the event page's anonymous who's-coming row — so an anon viewer and a signed-in viewer looking at hidden attendees see the same placeholder. Its colour is the slot's position in the row mod 5, never anything tied to the user, so a colour cannot follow a person across races (W-028).

The event detail page is a two-tier surface for signed-out visitors. The header (title, meta, hero image and photographer credit), the event `short_description` (both as visible prose below the hero and as the page's `<meta name="description">`, truncated to 160 chars by `truncate_for_meta`), the going / interested counts and the sign-in CTA are all rendered and crawlable. The description is anon-visible **by design, not by omission** — it is the page's SEO payload, so moving it behind the sign-in gate would defeat its purpose. It is scraped prose about the event itself and carries no per-user data, so it sits outside the privacy model entirely. The action bar carries counts and attendance buttons only; the avatar strips that used to sit there were removed as duplicates of the Who's coming section below. The race selector table, the race detail cards, and the elevation placeholder are gated behind a single `{% if current_user %} … {% else %} <locked panel> {% endif %}` in `event.html`, so the anon HTML source contains none of the scraped race fields — no distances, ascent, price, cutoff, registration or elevation markup. The gated slot renders a plain `.locked-panel` white card with a sign-in CTA. Both anon CTAs on the page (the attendance-bar `Sign in to join` and the locked-panel `Sign in to see race details`) link to `/auth/google?next={{ request.url.path }}`. The `next` value goes through `_validate_next` in `app/main.py` — accepted only when it starts with a single `/`, is not protocol-relative (`//`), does not start with `http:` / `https:` / `data:` / `javascript:`, and contains no CRLF, backslash or whitespace (the backslash reject closes a browser-normalisation bypass where `/\evil.com` is treated as protocol-relative by some parsers) — and is stashed into `session["post_login_redirect"]`, which the existing Google callback already pops with a fallback to `/`. No `state` round-trip is used; the same session key that carries the crew-invite post-login target is reused, and last click wins if both are stashed in the same session.

Below the race detail (for signed-in viewers) or as a sibling of the locked panel (for anon), the event page carries a "Who's coming" section — two columns (Going, Interested) with one row per visible attendee. `AttendanceService.get_attendance_summary` returns the full filtered identity lists, not just the four-name preview used by the action bar strip; the action bar continues to trim display via the shared `avatar_strip` macro's `cap` argument. Signed-in viewers see every attendee they are allowed to see plus, when relevant, a neutral line driven directly by `going_hidden_count` / `interested_hidden_count` — `N indie runner(s) is/are going` when nobody is named, `and N other indie runner(s) are going` under names (`hidden_line` macro, W-066). The line is worded identically whether the hidden attendees are `crews_only`-blocked or a not-yet-migrated `private` row, so it never leaks the reason. Anonymous viewers see the same two-column shell with anonymous avatars up to the display cap plus a `+N` overflow chip, and a quiet inline `Sign in to see who's going` / `Sign in to see who's interested` text link per column — intentionally lighter than the locked-panel primary CTA so the page has one primary action (race data) and one secondary nudge (identity). Each column is only rendered when its own count is greater than zero, and the whole section is skipped when the event has no attendees at all. Clicking Going / Interested from the action bar continues to update the strip and counts via `attendance.js`; the Who's-coming section only reflects the viewer's own change on the next page load.

`ProfileService.get_profile` returns a `ProfileView` with an `is_visible: bool` flag rather than raising, so the route can render `profile_hidden.html` — a generic "this runner keeps their profile private" placeholder with no name, avatar, or stats. The wording is identical for `private` and `crews_only`-blocked cases so a viewer cannot infer which reason fired. Anonymous visitors hitting `GET /profile/{user_id}` also see the placeholder — no enumeration signal.

The profile page states the owner's current level back to them. A summary line above the stats — rendered only when `viewer_is_self`, so it is absent for strangers and in preview mode — names the active level in the same language as the settings radios (`Public` / `Crews only` / `Private`), says what it means for the race calendar, and links to `/settings`. **The user-facing term for this control is "visibility", not "privacy", everywhere it is named** — it is the settings section heading, the `web.users.visibility` column, the form field, and `SettingsService.update_visibility`, so the UI copy and the CSS classes (`.profile-visibility*`) follow it. "Privacy" is reserved for the Privacy Policy linked in the footer, which is a different thing: a legal document about data handling rather than a per-user control. It replaced three per-section "Visible to your community" tags that were static text: they claimed one fixed level regardless of the user's actual setting, and they rendered for every viewer rather than only the owner. Wording tracks the real model — `public` reads "every signed-in runner", never "everyone", because anonymous visitors get `profile_hidden.html` at every level.

The visibility control lives on `GET /settings`, an authenticated page with an All indie runners / Crews only radio group. The viewer's crews are not there: since W-078 the own profile carries a My crews section (name, member count, link to the hub, "Create a crew"), rendered only when `viewer_is_self`, and the nav's Crews item is `GET /crews`, a 303 to the hub when the user has exactly one crew and to `/profile/{id}#crews` otherwise — a redirect so no signed-in render pays a crews query for the menu. `SettingsService.update_visibility` validates the level against `{'public', 'crews_only'}` and writes the column. `POST /settings` redirects to `/settings?saved=1` on success, which renders a green "Saved" flash so the user has visible confirmation of the write.

The settings page also links to `/profile/{id}?preview=1`, which drops the self short-circuit in `ProfileService` so the profile owner sees exactly what a signed-in stranger sees — crews-only targets render the placeholder, public targets render the public profile. Preview intentionally passes an empty `viewer_crews` set so a `crews_only` target renders as it would for a signed-in stranger with no shared crew. A yellow "Preview" banner marks the mode so the user does not read the result as a bug.

## Crews

A crew is a named group of users, invite-only, no public directory. Anyone signed in can create one via `POST /crews/new`; the creator is inserted with `role='admin'` and a fresh `web.crew_invites` row is issued in the same commit, so a brand-new crew has a shareable URL immediately (the post-create page IS the invite step — no second form field). Slugs are derived from the display name (lowercase, non-alphanumeric collapsed to `-`), and a name whose slug is taken is refused ("That name is taken"), not suffixed: two crews with one name were indistinguishable on the invite page (1.9.30). A slug in `_RESERVED_SLUGS` (`new`, which the create form's route shadows) or longer than the 64-character column is refused at the form too (1.9.32). The `UNIQUE` slug decides, so concurrent creates cannot both succeed.

Growth is via a single invite URL per crew (`/crews/join/{token}`), multi-use, revocable, no TTL. Admin-only rotate (`POST /crews/{slug}/invite/rotate`) sets `revoked_at=NOW()` on the currently active row and inserts a fresh one; the old URL then resolves to `crews_invite_invalid.html`. The invite URL itself is visible to every member (forwarding is the intended path); the security control is rotation, not readership.

Membership is the only knob that gates `crews_only` visibility. Given a viewer and an attendee, `AttendanceService` treats a `crews_only` attendee as visible iff `viewer_crews & attendee_crews` is non-empty. The same predicate governs `ProfileService`. Because visibility is evaluated at read time, joining or leaving a crew immediately changes what identities the viewer sees — no write-path work, no retroactive migration.

`GET /crews/{slug}` is member-gated: non-members and non-existent slugs both render `crews_hidden.html`, which surfaces no crew name or member list. For a member it is the crew hub (W-077): `CrewService.list_agenda` — the non-past occurrences members have marked, grouped by month, TBC under its expected month, every row with its going and interested members (the `?view=going` filter was removed in W-095 on Paulo's word; the parameter is ignored) — beside the Members and Invite sidebar. A dated edition is past once attendance on it is locked (W-072), one day before the index drops it. A signed-out visitor gets the same placeholder before any lookup, so a real and a made-up slug answer alike, with a Sign in link whose `next` is the URL asked for, query string kept (W-085); `/crews`, `/crews/new` and `/profile` answer anon with a 303 through sign-in and back instead. Crews are invite-only enough that guessing a real slug on the signed-in path is not a meaningful attack surface.

Three paths change `created_by` after insert, so read it as the current owner, not the historical creator: `POST /crews/{slug}/leave` (W-081, member-gated, Origin-checked by the middleware, 303 to the own profile with a flash), `POST /crews/{slug}/members/{user_id}/remove` (W-082, admin-gated, the actor cannot be the target, 303 back to the hub with a flash that offers Rotate; nothing stops the removed member rejoining with the current link) and account deletion (W-022). All go through `CrewService.remove_member`: a crew with no one else in it is deleted, and any other crew passes to its longest-standing remaining member, admins first: that member becomes admin and takes over `created_by` on the crew and its invites. The soft refs have no FK, so this rule lives in that one method and nowhere in the schema; `delete_account` loops over it and still refuses if a soft ref survives.

Small-crew leak: in a 2- or 3-person crew, an attendee count going 0 → 1 identifies the actor. Not solvable without k-anonymity work that would dwarf the rest of the primitive. The crew detail page showed a soft hint under 4 members ("small crews may reveal who is going — larger crews give more anonymity") from phase 3 PR3 (2026-07-17) to 1.9.61; W-095 removed it on Paulo's word. The leak itself is unchanged by that: the count still reveals the actor in a small crew.

## Index filtering

The index filter surface is two tiers of one `<form method="get" action="/">`. The always-visible `.filters-bar` carries search, distance range, date range and country. A collapsible `<details class="filters-advanced">` below it carries the advanced filters — race-format checkboxes and a cutoff-hours range. `<details>` was chosen over a JS toggle so open/closed state, keyboard operation and no-JS operation come for free; the panel renders `open` only when `has_advanced_filters` is true, so a shared `?format=relay` URL does not look like it lost its filters while a plain `?country=…` URL leaves the panel shut.

Every filter is an optional query parameter, so the URL contract is purely additive — any URL bookmarked before a filter existed still behaves identically. `_parse_filters` in `app/main.py` coerces all of them defensively: unparseable numbers and dates and blank strings degrade to `None`, and `formats` is whitelisted against `RACE_FORMAT_SLUGS`, so `?cutoff_max=abc` or `?format=zzz` cannot mark the filter set active, spring the panel open, or reach the query. The repeatable `format` parameter is declared `Query(default=[], alias="format")` — a bare `str` annotation silently keeps only one value, which would appear to work with one checkbox ticked and drop the rest.

Two flags come back to the template: `has_active_filters` (any filter at all, drives the "Clear filters" link) and `has_advanced_filters` (advanced fields only, drives the panel's `open` state).

Because filter values round-trip through `float`, a submitted `12` would re-render as `12.0`. The `trimnum` Jinja filter — registered on `templates.env` in `app/main.py` — drops a trailing `.0` from whole numbers while preserving real fractions, and returns `''` for `None`. All four numeric inputs (distance and cutoff, min and max) render through it.

See the RaceService entry under Service classes for how each filter is applied — in particular that the advanced filters are event-level ANY matches over race-level data, and why `race_format` cannot be filtered in SQL at all.

## HTTP method surface

Every route that serves a page is declared `@app.api_route(..., methods=["GET", "HEAD"])`, not `@app.get`. FastAPI's `APIRoute` binds exactly the methods named in the decorator and does **not** synthesise `HEAD` from `GET`, so a `@app.get` route answers 405 to the `HEAD` probe that link checkers, unfurl bots and uptime monitors send before fetching — which is what every public page did until 1.9.7.

`api_route` rather than an `@app.head` stacked beside each `@app.get` because **one declaration cannot drift out of sync with itself**: two decorators over one handler are two places to remember, and the next route gets written by copying a neighbour. The cost is a wordier decorator that no longer reads as the FastAPI idiom.

`HEAD` is not a widened surface. It runs the same handler and the same dependencies as `GET`, so an auth-gated route answers a `HEAD` exactly what it answers a `GET` from the same caller — anonymous `HEAD /settings` is a 401, not a 200 that would confirm the page to a crawler. `POST` routes are unaffected, and `/debug/health` deliberately keeps `@app.get`: it is not part of the public browse surface. Verified for the anon and signed-in tiers on the routes listed in the 1.9.7 changelog entry; the OAuth flow itself was not exercised.

## Crawl surface

`/robots.txt` disallows the signed-in surfaces (1.9.21) and points at `/sitemap.xml` (1.9.22). The sitemap lists the anon-public pages (`/`, `/stats`, `/imprint`, `/privacy`, `/terms`) and one URL per event from `RaceService.list_races(RaceFilters())`, the index's own unfiltered query before its 60-tile cut, so it cannot list an event the site would not render. **Built live per request, not cached:** about 400 rows, roughly 0.2 s locally, the same `list_races` cost `/stats` already pays, and a cache would add a TTL and with it a window where the sitemap lists an edition that has left the view. No `lastmod`/`changefreq`/`priority`: this app reads no per-event modification time, so a `lastmod` would be made up. Revisit caching or an index file if the corpus nears ~25,000 events. Verified against one local run on 2026-10-25 (1.9.22 changelog).

## Authentication

Google OAuth 2.0 with scopes `openid email profile`. Non-sensitive scopes — no Google verification review required. App runs in Testing mode (100-user cap). Sessions are managed via secure signed cookies.

Flow: `GET /auth/google` → Google consent screen → `GET /auth/google/callback` → exchange code for token → fetch userinfo → gate on `email_verified` → upsert `web.users` and `web.auth_identities` → set `session["user_id"]` → redirect `/`. A callback with no `code` (Google's Cancel sends `error=access_denied` and no `code`) pops `post_login_redirect` and answers `303 /` without touching `user_id` (W-092). A `code` Google refuses at the token endpoint (replayed after a reload or back, expired, bogus) raises `CodeExchangeRefused` from `GoogleAuthService` after one WARNING line carrying Google's `error` value and never the code; a session that already holds `user_id` is sent on with `303` to the queued redirect or `/`, a signed-out one gets `signin_failed.html` at `400` with a Try again link, its queued redirect left in place (W-094).

## Service classes

Business logic lives in focused service classes, one per domain:

- `GoogleAuthService` (`app/services/auth_service.py`) — builds Google authorize URL, exchanges auth code for token, fetches userinfo via httpx
- `UserService` (`app/services/user_service.py`) — upserts `web.users` and `web.auth_identities` from Google userinfo; gates on `email_verified`; `delete_account` removes a user in one transaction (DB cascades plus the crew rule under Crews)
- `RaceService` (`app/services/race_service.py`) — queries `core.v_denormalized_event_data_upcoming` (a view over `core.mv_denormalized_event_data` owned by indie-runners-scraper; filters the MV down to rows that actually belong to the current occurrence, so stale prior-edition races no longer bleed into fresh TBC / upcoming occurrences), groups rows by event, applies filters, assigns gradient classes. Since scraper migration 025 the underlying MV also carries `tbc` occurrences alongside `upcoming` / `current`, with `occurrence_status` and `occurrence_expected_month` columns; a `tbc` row is admitted, and judged by the date filters, on its expected-month-start `make_date(occurrence_year::int, COALESCE(occurrence_expected_month::int, 12), 1)`, even when it carries an inherited `race_date`; the SQL `ORDER BY` alone uses `COALESCE(race_date, <that>)`, for the reason given under filtering below. Tile face reads "October 2027 (TBC)" via `format_tbc_expected(year, month)` when `is_tbc`, and the hover panel drops Distances / Location / Entry-fee (all NULL on TBC rows) for a single muted notice line. The route-level tiebreaker in `app/main.py` at the end of `index()` re-sorts the fetched rows by engagement first (`going_count`, `interested_count`) then by best-known expected date — for TBC rows that means `expected_year` / `expected_month`, not `race_date`, because scraper migration 029's LATERAL prior-edition fallback populates `race_date` with the previous edition's date and would otherwise leapfrog zero-engagement TBC events to the top of the zero-engagement bucket.
  Filtering is split by necessity. `distance_min` / `distance_max` / `date_from` / `date_to` / `country` / `search` are applied where they can be — dates and country in the SQL `WHERE`, distance post-grouping. The date filters judge a `tbc` row by its expected month (December if null) even when it carries a `race_date`, because that date is last edition's, inherited (scraper contract 2026-09-05); `ORDER BY` stays on `race_date`, which is still what orders an event's races for first-see. The advanced filters (`formats`, plus `cutoff_min` / `cutoff_max`) are applied **post-grouping** because tiles are event-grained while the underlying fields are race-grained: an event matches if **any** of its races match, so multiple checked formats read as OR. `race_format` additionally cannot be filtered in SQL at all, since the MV stores it as a JSON array string rather than a queryable relation. `cutoff_time` *could* be filtered in SQL but deliberately is not: a race-level `WHERE` would drop an event's non-matching race rows before grouping and silently corrupt the tile's distance list and date span, so the tile would describe only the races that passed the filter rather than the whole event. Note one deliberate asymmetry in the empty-set rules — an event with no distance data passes a distance filter, but an event with no cutoff data is **excluded** by a cutoff filter, because asking for a cutoff range implies asking for races whose cutoff is known. Cutoff coverage is partial (149 of 356 events, measured 2026-08-28; 57 of 234 on 2026-08-08), so a cutoff filter first drops every event without one, still the majority, and only then compares hours. It cuts harder than its hour range suggests for as long as most events lack a cutoff. `RACE_FORMAT_CHOICES` is the single source for both the rendered checkboxes and the whitelist that incoming `?format=` values are validated against; it is a static list, not a `DISTINCT` query, and a new scraper slug means adding an entry there.

  Alongside the query methods, `race_service.py` hosts the module-level display helpers shared by the index and event routes: `format_date_range`, `format_tbc_expected`, and the race-format family `parse_race_formats` / `format_label` / `race_format_labels`. The last three exist because `race_format` is projected by the MV as a **JSON array serialised to text** (`'["backyard_ultra", "timed"]'`) — a race can carry more than one format. `parse_race_formats` returns `[]` for every unusable shape (NULL, malformed JSON, JSON scalar, blank members) so callers need no guards, and `format_label` title-cases slugs it does not recognise rather than dropping them, so a new scraper value degrades to readable text instead of disappearing. Coverage is sparse — 90 of 356 events carry any format (measured 2026-08-28) — so consuming surfaces must render nothing rather than an empty affordance when the data is absent.
- `AttendanceService` (`app/services/attendance_service.py`) — upserts and deletes `web.attendance` rows keyed by `occurrence_id`; snapshots `race_date` and `event_display_name` at mark time; refuses mark and delete once the occurrence's last day has passed (`is_locked`, also read by the tile and event page); returns per-occurrence going/interested counts plus up to 4 going and 4 interested avatars filtered by each attendee's `visibility` against the viewer id and `viewer_crews` set (anon → empty identity lists; self is always visible; `crews_only` visible iff shared crew)
- `ProfileService` (`app/services/profile_service.py`) — builds three shelves (going upcoming, going past, interested) from `web.attendance` joined to `core.events` and `core.event_occurrences`, plus two lists of `TimelineRow(row, flag)` derived from them: `upcoming_timeline` (going and interested interleaved, by month then date, a TBC edition last under its expected month — December if unknown — the crew hub's rule, W-098) and `past_timeline` (been-there rows, most recent first). Each `TimelineRow` carries its `month`, so the template prints the hub's month heading when it changes and does no date arithmetic. The shelves survive because the stat boxes count them; the timelines are what the page lists. `flag` is `been_there` / `going` / `interested`, derived once in the service so the template does no date arithmetic. Past races are a **separate list rather than the tail of one merged timeline** — sorting everything by date put a long history above the races a runner still has ahead of them. Loads target user + visibility; takes `viewer_crews` and returns `ProfileView(is_visible=False)` when target is missing (to avoid enumeration), or `crews_only` and viewer shares no crew, and the viewer is not the target. **A row links to its event page only when the serving view still serves it** (`ProfileRow.has_page`, an `EXISTS` on the view in the same query): the profile reads `core.*` tables that keep every occurrence, the event page reads the view, which drops a non-TBC race the day after it runs **Location and terrain come from the MV, event-level** (W-027): `core.events.location` / `event_type` are NULL on every row. The attended edition wins when the MV still holds it; otherwise the edition it does hold supplies them, which assumes a series keeps its start town and terrain. On 2026-10-25 that was 29 of 46 attendance rows. Location is `event_location()` over the attended edition's MV rows where it has any, else all of the event's rows (W-070; one query for every attended event, grouped in Python); terrain the longest race's (the hero's), `mv_id` breaking ties.
- `SettingsService` (`app/services/settings_service.py`) — validates and writes `web.users.visibility`. Selectable set is `{'public', 'crews_only'}` (W-076).
- `CrewService` (`app/services/crew_service.py`) — crew CRUD (`create_crew`, `get_crew_by_slug`, `list_crews_for_user`), the hub agenda (`list_agenda`: one attendance read, one MV read, grouped in Python), membership (`is_member`, `is_admin`, `list_members`, `add_member`, `shares_crew_with`), the visibility-thread helpers (`get_viewer_crew_ids`, `get_attendee_crew_ids`), and invite lifecycle (`active_invite_for_crew`, `rotate_invite`, `find_crew_by_invite_token`). `create_crew` inserts crew + admin membership + fresh invite in one commit, so a new crew has a live invite URL immediately.

## Session management

`starlette.middleware.sessions.SessionMiddleware` is added to the app, signing cookies with `SECRET_KEY`. Cookie settings: `httponly=true`, `samesite=lax`, `secure=true` in production (`DEBUG=false`), `secure=false` in local dev (`DEBUG=true`). The `user_id` is stored in the session after successful OAuth. After login the callback pops `session["post_login_redirect"]` (set by routes like `GET /crews/join/{token}` when a signed-out visitor lands on an auth-required URL) and redirects there, falling back to `/`. Only server-set redirects are honoured; there is no `?next=` query parameter, so no open-redirect surface.

There is no CSRF token. SameSite=lax covers cross-site POSTs, but a sibling subdomain is same-site, so `SameOriginMiddleware` refuses every non-GET/HEAD/OPTIONS request whose `Origin` host differs from `Host` (403, W-031). A missing `Origin` passes: a browser attaches it to every POST and DELETE, form or fetch, so a sibling page cannot omit it, and a non-browser client already needs the cookie. `Origin: null` has no host and is refused. That holds only while no page sets a document-level `no-referrer` policy (meta tag or `Referrer-Policy` header): under one, a browser form submit sends `Origin: null` and every form answers 403. Per-`<img>` `referrerpolicy` does not count. The event page's "← All events" link leans on the same policy: it rebuilds the filtered index from the `Referer`'s query when the referrer is this host's `/`, and is `/` otherwise (W-102). Only the query is copied, behind a literal `/?`, so it cannot point off the index. `GET /auth/logout` is the one state change outside the rule, accepted because a forced logout is a nuisance, not a loss.

## Stats page

`GET /stats` is public, linked from the footer, and states **two counts
that are never combined** (Paulo, 2026-10-21): "events tracked" is
`core.events` with `status = 'active'`, stable all year, and "events
checked in the last 30 days" is distinct `event_id` in the serving view by
`event_last_checked_at`. A fraction of the two would divide numbers from
different sets. The list is the last 10 checked, with no age filter, linked
from view rows, so every link resolves. Three aggregate queries, ~7 ms.

## Legal pages

`GET /imprint` and `GET /privacy` render static Jinja templates
(`imprint.html`, `privacy.html`). Both are anon-accessible and linked
from the footer on every page, so they are reachable within one click
from any URL, signed-out included. The imprint carries the § 5 DDG
legal notice; the privacy policy documents the actual data inventory
(Google OAuth profile fields, attendance rows, session cookie, GCP
server logs) — not aspirational boilerplate. Data deletion requests
are handled by email at `paulo@indierunners.co` with a 30-day response
window; there is no self-service delete route today.

The privacy policy's EU-US transfer wording references Google's EU-U.S.
Data Privacy Framework certification supplemented by Standard
Contractual Clauses (Commission Implementing Decision (EU) 2021/914).

The site uses GoatCounter (`indierunners.goatcounter.com`) as its
analytics tool, loaded via a single async `<script>` tag in
`app/templates/base.html`. GoatCounter is cookieless and does not
identify individual visitors across sessions or sites, so no consent
banner is required under the ePrivacy Directive. Section 5 of the
privacy policy ("Analytics") documents what is collected, the 365-day
retention window, and the no-third-party-sharing guarantee. Before
adding any additional analytics or tracking that *does* set cookies or
identify individuals, section 5 must be rewritten and a cookie consent
banner must ship at the same time — the current policy commits to
cookieless, session-scoped tracking only.

## Database connections: a shared, small budget

The Cloud SQL instance is shared with the scraper project, and it is
`db-f1-micro` — 614 MB RAM and **`max_connections = 25`**. That total is not
what is available:

| | Connections |
|---|---|
| `max_connections` | 25 |
| − reserved for superusers | −3 |
| − held permanently by the Cloud SQL agent | −3 |
| **Available to applications** | **19** |

Those 19 are shared between this service and the scraper's batch pipelines,
which take **6–8 each** while running (their Phase 5 processes three races
concurrently in a thread pool, and each thread opens its own connections).

**The pool is therefore capped, and the cap is load-bearing.** `app/db.py` sets
`pool_size=2, max_overflow=0`, giving 2 connections per instance and **10 at
`maxScale=5`**.

Left uncapped, SQLAlchemy's defaults (`pool_size=5, max_overflow=10`) allow 15
per instance and 75 across five — roughly four times the entire budget. **The
idle case is the one that bites**: overflow connections close when returned,
but pooled connections are held persistently once warmed, so after a single
traffic spike this service alone would hold 25 connections indefinitely, with
nothing releasing them. The site would sit idle while the scraper could not
connect at all.

Three companion settings exist because of the cap, not alongside it:

- **`pool_pre_ping=True` and `pool_recycle=1800`.** Cloud SQL drops idle
  connections. A capped pool makes each connection longer-lived, so without
  these the cap would trade exhaustion errors for stale-connection errors.
- **`pool_timeout=10`** (down from the 30s default). Handlers are sync, so
  FastAPI runs them in a threadpool of roughly 40 against a pool of 2. On
  saturation a request should fail fast rather than hold a thread for 30
  seconds.
- **`application_name`** carrying `K_REVISION`. Without it this service's
  connections show as `(unnamed)` in `pg_stat_activity`, indistinguishable from
  every other client on a shared instance.

**Consequence to keep in mind.** `max_overflow=0` means requests beyond two
concurrent database users **queue** rather than opening more connections, so
exhaustion presents as latency rather than errors. Sluggishness under load is
the signal that 2 is genuinely too small — raise it and re-measure rather than
removing the cap. The live figure:

```sql
SELECT application_name, state, count(*)
FROM pg_stat_activity WHERE backend_type = 'client backend'
GROUP BY 1, 2 ORDER BY 3 DESC;
```

**Any new connection source counts against the same 19.** Scripts under
`scripts/` import `SessionLocal` and therefore build their own pool when run
manually; running one during a batch pipeline adds to the contention. A second
engine, an async engine alongside the sync one, or a `--workers` flag on
uvicorn would each multiply the per-instance figure silently.

Raising `max_connections` without raising the tier is not a fix: each
connection costs roughly 10 MB of RAM against the instance's 614 MB, so the
failure would move from refused connections to memory exhaustion. More
connections require a larger instance (`db-g1-small` allows ~100).

## Configuration

All configuration is read from environment variables via `app/config.py`. See `.env.example` for the full list. The `DATABASE_URL` single-variable approach covers both local TCP and Cloud SQL Unix socket connections.

Required variables:
- `DATABASE_URL` — SQLAlchemy connection string (`postgresql+psycopg://...`)
- `SECRET_KEY` — signs session cookies; rotate on deploy to invalidate existing sessions
- `DEBUG` — `true` in local dev, `false` in production
- `PORT` — port to bind (Cloud Run sets this automatically)
- `GOOGLE_CLIENT_ID` — from Google Cloud Console
- `GOOGLE_CLIENT_SECRET` — from Google Cloud Console
- `GOOGLE_REDIRECT_URI` — callback URL registered with Google (prod: `https://indierunners.co/auth/google/callback`)
- `TILE_VERSION` — tile prefix served for event tiles. Default lives in `app/config.py` (currently `v02`); the env var only needs setting to override for a temporary trial. Corresponds to `gs://indie-runners-web-tiles/tiles/<version>/`. To make a new version permanent, edit `app/config.py`, commit, redeploy.

Optional, workstation only:

- `UNSPLASH_ACCESS_KEY` — read by `scripts/unsplash_fetch.py`. Never read by the
  app and not needed on Cloud Run. It is nonetheless **declared** on `Settings`,
  because `BaseSettings` defaults to `extra_forbidden`: an undeclared key in
  `.env` raises on every import of `app.config`, which takes down `uvicorn` and
  every script with it. The error names the offending field but not the cause,
  so it reads like a config bug rather than a stray line in `.env`. Any future
  local-only variable needs the same treatment.

## Static assets

Tile images live in a dedicated public bucket, `gs://indie-runners-web-tiles`,
and are produced by the offline pipeline under `app/imaging/`. Operational
reference — bucket layout, CLI, add-a-photo, bump-a-version — is in
`docs/IMAGING.md`.

Dedicated is now the common case, not the exception: 166 of 246 events
(counted 2026-08-12, 1.8.1) carry their own photo, sourced via `scripts/unsplash_fetch.py`. Stock is
the fallback for the rest — events with no `race_location` to search on,
events sharing a location with another event already using that city's
landmarks, and small races in places Unsplash has not photographed. See
`docs/IMAGING.md` for why the remainder was left rather than converted.

At app startup, `app/imaging/dedicated_index.py` performs one anonymous
`list_blobs` call against `originals/dedicated/` and caches the resulting
set of event slugs on `app.state.dedicated_slugs`. The resolver checks
this set to decide dedicated-vs-stock per tile; the DB is not consulted
for that decision. To pick up a newly published dedicated photo, restart
the app.

Two request paths consume the pipeline output: the index route resolves
one tile URL per race listed on `/`, and the event detail route
(`GET /events/{event_slug}/{occurrence_year}`) resolves one hero image
URL for the page header. Both call `EventImageService.get_or_create_for_events`
(the detail path passes a one-item list) and then `resolve_tile_image`
with the same `request.app.state.dedicated_slugs` set. The hero also
surfaces the photographer credit from three columns on `web.event_images`
(`attribution_name`, `attribution_url`, `attribution_source_url`),
rendered as a small pill in the corner. All three columns are nullable
and the template degrades gracefully — full Unsplash-compliant two-link
form when everything is set, plain-text `Photo · {name}` when only the
name exists, nothing when the name is null.

Photographer credits are populated automatically from two checked-in
manifests generated offline from the credits docs:

- `app/imaging/stock_manifest.json` (from `docs/stock_credits.md`) —
  used at stock assignment time. `EventImageService.get_or_create_for_events`
  writes the three attribution columns on every new insert.
- `app/imaging/dedicated_manifest.json` (from `docs/dedicated_credits.md`)
  — used at startup. Right after `load_dedicated_slugs()` populates
  `app.state.dedicated_slugs`, the startup hook calls
  `EventImageService.refresh_dedicated_attributions` which rewrites
  the three columns for any row whose event is dedicated. Idempotent.

For the initial data rollout, or after wide manifest edits, the
one-shot `scripts/backfill_event_image_attribution.py` sweeps every
row and writes the columns from whichever manifest applies. See
`docs/IMAGING.md` for the full ops flow.

**Publishing a dedicated photo without restarting credits the wrong
photographer.** The image resolves by slug the moment the blob lands in the
bucket, but the credit pill reads `web.event_images`, whose attribution columns
are only rewritten by the startup hook. Between publish and restart the tile
therefore shows the new photo under the *stock* photographer's name — the
licensing bug the heal's dedicated-skip rule exists to prevent, arriving by a
different route. It is silent: the photo is right, the profile link resolves to
a real photographer, and nothing errors. This bit 16 events at once during the
1.8.0 batch. A restart only rewrites slugs in the manifest baked into the
serving image, so for photos published since that image was built,
`scripts/backfill_event_image_attribution.py` is the fix (W-104).

Terrain assignment: `EventImageService.get_or_create_for_events` inserts one
row per event on first tile render with `on_conflict_do_nothing`, and
`_normalize_terrain(None)` returns `mixed`. So an event first rendered while
its source `terrain_type` is still NULL (typically a TBC occurrence before the
organiser publishes race details) is assigned `terrain='mixed'` and a `mixed_*`
stock file. That assignment used to be permanent even after the scraper
populated the real terrain; `_heal_defaulted_terrain` now repairs it on read.

The heal is deliberately narrow, and the narrowness is what makes it safe
without a schema change:

- **Only rows stored as `mixed` are candidates.** That value is the observable
  signature of the NULL default — a legitimately-mixed event has a source
  terrain that normalizes to `mixed` as well, so it never triggers. This is why
  no `terrain_source` column (and therefore no migration) is needed.
- **Only a source terrain of `road` / `trail` fires a rewrite**, so once a row
  is repaired it can never be touched again. Events whose races carry
  conflicting terrain values therefore cannot flap on every page view depending
  on which race row is read first.
- **A stored `road` / `trail` whose source now reads `mixed` is left alone.**
  That direction was judged a scraper regression when
  `scripts/backfill_event_image_terrain.py` shipped; the heal keeps that policy.
- **Dedicated slugs are skipped.** The resolver serves those from their own
  photo and ignores `stock_filename`, so repairing one would put a stock
  photographer's credit under a dedicated image — a licensing bug, not a
  cosmetic one. Healing is therefore opt-in per call site: `get_or_create_for_events`
  only heals when passed `dedicated_slugs`, so a caller without the slug cache
  cannot trigger it.

The repair commits on **its own short-lived Session**, never the request's,
because healing is opportunistic maintenance and should be transactionally
independent of the render. That argument is the whole reason now, and it always
stood on its own.

It is no longer also a workaround. Committing the request session expires every
object loaded in it, including the `core.Race` rows the caller is still
iterating, and reloading an expired `Race` used to fail outright against the
`mv_id` type mismatch above — so a commit on the shared session would 500 the
page. W-007 fixed that at the cause (2026-08-28); the heal's own design is
unchanged, and the constraint it was navigating is gone.

`scripts/backfill_event_image_terrain.py` remains for bulk sweeps but is no
longer needed routinely — rows now heal as their pages render.

## Migration safety rules

Migrations that delete rows have destroyed production data before. Follow these rules without exception:

1. **Always inspect before deleting.** Run a `SELECT COUNT(*)` (and a sample `SELECT *`) on any rows the migration will delete before running the destructive step. Confirm the count with the team.
2. **Split backfill from delete.** Never put a `DELETE` in the same migration step as a `UPDATE` backfill. Run the backfill, verify row counts match expectations, then delete in a separate step.
3. **Verify join logic on real data.** Before writing a backfill `UPDATE ... FROM`, query both sides of the join separately to confirm the keys actually match. Do not assume column names or types — check them.
4. **Confirm point-in-time recovery is on** before running any destructive migration on production: `gcloud sql instances describe indie-runners-db` shows `pointInTimeRecoveryEnabled: true`. Note the UTC time you start; that is the restore point. Do not take a manual snapshot: an on-demand backup never expires, so it keeps deleted accounts past the 7 days privacy §8 promises.
   *Why (W-033):* on 2026-06-17, the day migration 002 was committed as run (its TODO), the 03:42 UTC automated backup was restored into a side instance (`indie-runners-db-restore`, 16:39 UTC, Cloud Audit Logs) and deleted at 17:44; these rules were committed at 17:29. So a restore was needed that day, and the newest restore point was 13 hours old. Rule 4 asked for a fresher one. PITR, on since 2026-07-27, gives a restore point to the second without a copy that outlives §8. Whether rows were finally lost is not in the logs.
5. **Unmatched rows = stop.** If a backfill leaves any rows un-updated (i.e. `WHERE new_column IS NULL` returns rows), stop and investigate before proceeding to the delete step.
6. **A restore brings back deleted accounts; delete them again before anything leaves the clone.** Restore into a new instance, never over `indie-runners-db`: PITR always clones (DEV_NOTES 2026-10-26, W-033), but `gcloud sql backups restore --restore-instance=indie-runners-db` overwrites production, and then there is no live `web.users` to compare against. Every account deleted after the restore point is alive in it, and privacy §8 promises it is gone. To find them, compare `SELECT id FROM web.users` on production and on the clone. Ids come from a sequence and are never reused, so an id in the clone but not in production was deleted after the restore point. Delete each one on the clone with `UserService.delete_account` (`DATABASE_URL` pointed at the clone), not a raw `DELETE`, because crew ownership is a soft ref with no FK. Check the count against the request log: one `303` per self-serve deletion, `httpRequest.requestUrl:"/settings/delete-account" AND httpRequest.status=303`, from the restore point on (`_Default` bucket, 30 days). Deletions done by hand on an email request (terms §9, privacy §8) leave no `303`; count those from the mailbox.
   *Limit:* the id diff is only right while production's `web.users` is intact. If the restore is *because* users rows were lost, lost and deleted accounts look the same, and nothing records which ids were deleted (DEV_NOTES 2026-10-26, W-032). Then the 303 count and the mailbox are all you have.
7. **CI applies every migration to a copy of `core.*`, once the file is in a PR or on `master`.** Branch pushes run no CI. The `migrations` job loads the scraper's `baseline.sql` at a pinned SHA and runs `migrations/` in order (W-054, 1.9.36). Green means names and types resolve against `core.*` at the pinned scraper ref, which is bumped by hand and can lag live. It does not mean a backfill is right: the tables are empty. Rules 1-5 still apply to live.

## CSS variables

All design tokens are declared in `:root` in `static/css/main.css`. Two separate link-color tokens exist to handle different surface types:

| Variable | Value | Use |
|---|---|---|
| `--forest-mid` | `#2d4430` | Links on light backgrounds (event detail page) |
| `--link-on-dark` | `#7db87a` | Links on dark backgrounds. Currently unused — its former consumer, the tile hover overlay's event-name link, was removed when the whole tile became the click target (1.4.0) — but kept declared for any future dark surface |

When adding links on a dark-background surface, always use `--link-on-dark` rather than `--forest-mid`. The two tokens carry the same "links are green" language at appropriate contrast for each surface.

## Local development

The Cloud SQL Auth Proxy (v1) is used to tunnel a TCP connection to the Cloud SQL instance on `localhost:5432`. The easiest way to start everything is:

```bash
bash scripts/dev.sh
```

This starts the proxy (skipping it if port 5432 is already in use) and then launches `uvicorn app.main:app --reload` on `http://localhost:8000`. Ctrl+C stops both. If you need the proxy standalone (e.g. to run psql), use `bash scripts/db_proxy.sh` instead.

The active gcloud account must have the `cloudsql.client` role on the project (`paulo@indierunners.co`).

The `DATABASE_URL` in `.env` uses the `postgresql+psycopg://` driver prefix required by SQLAlchemy 2.x with psycopg 3. The plain `postgresql://` prefix (used by psycopg 2 and psql) does not work with this setup.

**Private-term hook (W-111).** Once per clone, run `git config core.hooksPath .githooks`
(the setting lives in the shared `.git/config`, so worktrees get it too). `git commit` and a
merge that makes a commit (`pre-merge-commit`, W-114) then refuse an added line, an added,
renamed or copied path, or a commit message, that contains a term from
`exports/private-terms.txt` in the main checkout (untracked, one term per line, any case).
It refuses when that file is missing or has no non-blank term too. The refusal names the file
and line (or `filename hit`) and the term. `--no-verify` skips it on purpose. It does not scan
whole files, history, or what cherry-pick and rebase replay; a fast-forward makes no commit.

**Cache policy for `/static/` (1.9.48, W-074 / W-064).** The templates write no `/static/`
path by hand (`GET /favicon.ico` still redirects to the unversioned icon, so that one revalidates); `static_url('css/main.css')` renders `/static/css/main.css?v=<8 hex of md5>`,
computed once per process from the file in the image. `StaticCacheMiddleware` answers a
versioned path with `Cache-Control: public, max-age=31536000, immutable` and any other
`/static/` path with `no-cache`. Before 1.9.48 there was no header at all and a browser kept a
file for as long as it chose: Paulo's Firefox ran a pre-W-023 `attendance.js` for three days
after the popup shipped, which is W-074. Verified locally on 2026-10-30 (changelog 1.9.48); the
brand pack under `static/brand/` is served the same way but its generator is not touched.

## Deployment

Deployed to Google Cloud Run (`europe-west1`, service name `indie-runners-web`). The app binds `0.0.0.0` and reads `PORT` from the environment (Cloud Run sets it to `8080`). Cloud SQL (`indie-runners-dev-470411:europe-west10:indie-runners-db`) is connected via the Unix socket injected by the Cloud Run sidecar — the `DATABASE_URL` uses the `?host=/cloudsql/...` socket path.

Secrets (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SECRET_KEY`, `DATABASE_URL`) are stored in Google Secret Manager and injected as environment variables. The service runs under the `indie-runners-web@indie-runners-dev-470411.iam.gserviceaccount.com` service account, which has `Cloud SQL Client`, `Secret Manager Secret Accessor`, and `Cloud Run Invoker` roles.

The container image is built via Cloud Build and stored in `gcr.io/indie-runners-dev-470411/indie-runners-web`. To redeploy:

```bash
bash scripts/deploy.sh          # build and deploy
bash scripts/deploy.sh --check  # print the serving revision, change nothing
```

**Rollback is by revision, not by image tag.** The image is pushed untagged and overwritten every deploy, so it identifies nothing after the fact; the Cloud Run *revision* is the only durable handle on what was serving. `deploy.sh` therefore reads the serving revision before traffic moves and prints a `update-traffic --to-revisions=<name>=100` line naming it afterwards. This is a deliberate divergence from the scraper's `deploy.sh`, which rolls back by image tag read from its changelog: that repo tags images with a version, this one does not, so importing the version-read would create a second source of truth guarding nothing.

The service is configured `latestRevision: true`, so rolling back **pins** traffic and the next deploy produces a revision serving nobody. The script says so where it prints the rollback line, and prints `--to-latest` to undo the pin.

`deploy.sh` refuses a dirty working tree: an image built from uncommitted code cannot be rebuilt from git, so the revision it produces has no reproducible source at the moment one is needed. There is no test gate because there is no test suite (backlog `W-003`) — a gate on a suite that does not exist would be a comment rather than a guard.

Two custom domains are mapped via Cloud Run domain mappings (supported in `europe-west1`), declared in `indie-runners-infra/web/domains.tf`: `indierunners.co` (canonical) and `www.indierunners.co`. `beta.indierunners.co` was unmapped on 2026-11-09 (W-018); its OAuth callback was removed first. `CanonicalDomainMiddleware` in `app/main.py` 301-redirects `www` (and `beta`, still in `_REDIRECTED_HOSTS`, though it no longer reaches the app) to the apex host so all served responses come from `indierunners.co`. The middleware is registered after `SessionMiddleware` so it runs outermost — non-canonical hosts short-circuit before session, DB, or template work. 301 since 2026-10-22 (1.9.12, live from the next deploy). It was 302 from the apex rollout on 2026-07-27, so a rollback would not be cache-locked in browsers; browsers now cache the redirect, so reverting it takes their cache expiring, not a deploy.

Uvicorn is started with `--proxy-headers --forwarded-allow-ips='*'` (see `Dockerfile`) so `X-Forwarded-Proto` from Google Frontend is honoured. Without this, `request.url.scheme` is `http` inside the container and any absolute URL built from `request.url` (canonical-host redirect, `request.url_for` for invite links, `post_login_redirect` stash) leaks an `http://` scheme. Trusting `*` is safe on Cloud Run because the container is only reachable via Google Frontend; do not copy this pattern to a service with direct public ingress.
