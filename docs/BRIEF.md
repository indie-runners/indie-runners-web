# Brief: Event page — three sequenced changes

## What this covers

Three related changes to the event detail page
(`GET /events/{event_slug}/{occurrence_year}`, already auth-optional), to be
built and shipped in order:

1. **Hero image and photographer credit** — put the event photo in the header
   with a small credit.
2. **Anonymous gating** — turn the page into a teaser for signed-out visitors:
   name, hero, location, date and counts stay visible; the scraped race data
   becomes a sign-in gate.
3. **Participant list** — for signed-in viewers, show the names of who is going
   and interested, filtered by each attendee's privacy tier.

## Design reference (how to use the prototype files)

Alongside this brief there are standalone HTML prototypes showing the target look
for the hero, the locked panel, the grey avatar placeholders, and the two-column
"Who's coming" section. Use them as a visual reference only, not as code to port.

- Match the visual result — layout, spacing, the hero gradient treatment, the
  locked-panel look, the credit pill placement, the two-column participant layout.
- Implement it with the existing template structure, the existing CSS classes
  (for example `.avatar--stock`, `.detail-card`, `.race-selector`) and the design
  tokens already in `static/css/main.css`. Only add new classes where this brief
  calls for them.
- Do not copy from the prototypes: their inline `<style>` blocks, their invented
  class names, the JavaScript view toggles, the browser-side privacy filtering
  (privacy is decided server-side in the real app), the inline SVG stand-in for
  the hero (the real hero is the resolved tile image), or the mock roster data.

The brief is the source of truth for what to build. The prototypes are only what
it should look like when done.

## Why this order

All three touch the same surface: the attendee area and the split between what
anonymous and signed-in visitors see. The order removes rework:

- The **hero image is always visible to everyone**, so it has no gating logic.
  Doing it first is safe and it settles the final header layout before any
  conditionals get added inside the header.
- **Gating defines the anonymous half** of the attendee experience (grey
  placeholder circles, sign-in prompt, locked panel) and the reusable pieces the
  next phase needs (a grey avatar class, a sign-in URL that returns the user to
  the event page, the locked-panel pattern).
- The **participant list adds the signed-in half** (filtered names) and, for
  anonymous visitors, simply reuses the gate built in phase 2 instead of
  inventing its own.

Phases 1 and 2 are each independently deployable. Ship and deploy between phases.

## Confirm before starting (two data questions)

These are the only unknowns. Neither blocks phase 2.

- **Photographer attribution (affects phase 1 credit only).** The
  `web.event_images` table has an `attribution` column, but the credits may still
  live only in the markdown docs (`docs/stock_credits.md`,
  `docs/dedicated_credits.md`) and not in that column. If the column is not
  populated, the hero *image* still ships; the *credit* renders only where
  attribution exists and is otherwise omitted. Backfilling the column from those
  docs is a separate task, not part of this work.
- **Filtered interested list (affects phase 3).** Confirm
  `AttendanceService.get_attendance_summary(viewer_user_id)` returns a
  privacy-filtered `interested_users` list the same way it returns `going_users`.
  If it only returns going, add the interested list to the service first; the
  template must not do any privacy filtering itself.

Already decided: the gate uses a plain locked panel, not a blurred preview
(reason in phase 2). The sign-in-returns-to-event redirect is in scope
(phase 2).

## Shared conventions

- Template and route logic only across all three phases. No scraper changes, no
  schema changes.
- Keep every visibility, image-resolution, and redirect decision in the route or
  service layer. The template only branches on `current_user` and renders the
  view model it is handed.
- Any Python log messages use plain English, no special characters or
  exclamation marks (for example: `resolving hero image for event page`).
- Confirm exact file paths before editing. Expected files:
  `app/templates/event.html`, `static/css/main.css`, `app/main.py`,
  `app/services/event_image_service.py`, `app/services/attendance_service.py`,
  `app/services/auth_service.py`.

---

## Phase 1 — Hero image and photographer credit

### Objective
Show the event's tile image in the page header, with the title and meta over it,
and a small photographer credit. Visible to everyone, signed in or not.

### Scope
- `app/main.py` (event detail handler) — resolve the image and attribution for
  the single event and pass them into the template context.
- `app/services/event_image_service.py` — reuse the existing image resolution.
  The tile image pipeline (`EventImageService`, `resolve_tile_image`, the
  `tile_image_url` used on the index grid) already exists; it is only wired into
  the index route today. Add a path to resolve one event's image (and its
  attribution string) for the detail route. Do not duplicate the resolver.
- `app/templates/event.html` — restructure the header so the image sits behind
  the type badge, title, meta and website link, using the same dark gradient
  overlay treatment as the index tiles so the two pages read as one product.
- `static/css/main.css` — hero styles and the credit element. Reuse existing
  tokens and the tile gradient; introduce no new colors.

### Implementation notes
- The credit is a small, unobtrusive caption over the image (for example a pill
  in a corner reading `Photo · <name>`), optionally linking out.
- Graceful degradation: wrap the credit in `{% if tile_attribution %}` so it
  simply does not render when attribution is missing. This lets the phase ship
  before any attribution backfill.
- This phase establishes the final header layout. Later phases modify the avatar
  row inside this header but do not restructure it again.

### Acceptance criteria
- Event page renders the hero image in the header for both anonymous and
  signed-in visitors.
- Where attribution exists, the credit shows; where it does not, no credit
  element and no empty box appear.
- Header is responsive to mobile; title stays legible over the image.

---

## Phase 2 — Anonymous gating

### Objective
For signed-out visitors, keep the page browsable and crawlable — name, hero,
location, date and the going/interested counts stay visible — but gate the
scraped race data behind a sign-in prompt. Teaser, not a hard wall. The page
must still return 200 with real, indexable content for anonymous requests.

### Gating rule (decided: plain locked panel)
Render a plain locked panel with a sign-in prompt in place of the gated sections.
Do not render the real data and blur it with CSS: the scraped content would still
sit in the HTML source, which defeats the gate. For anonymous visitors the real
race data must never be written into the response at all. (A blurred *skeleton*
preview with no real values is a possible later iteration, not in scope now.)

### Element by element (keys off `current_user`)
- **Hero, counts, website link** — unchanged, visible to all.
- **Avatar row** (currently renders `attendance_summary.going_users[:4]` with
  real photos and colored-initial fallback):
  - Signed in: unchanged.
  - Anonymous: neutral grey placeholder circles, one per attendee up to four,
    driven by the count, no photo, no initial, no name; keep the existing `+N`
    overflow badge when the count exceeds four. Reuse the existing
    `.avatar--stock` grey circle if it renders with no glyph, otherwise add
    `.avatar--placeholder`. The colored-initial fallback must only ever render
    for signed-in viewers.
- **Race selector table** and **race detail panel** (with its cards and the
  elevation placeholder):
  - Signed in: unchanged.
  - Anonymous: render neither. Wrap both in one
    `{% if current_user %} ... {% else %} <locked panel> {% endif %}` and show a
    single combined locked panel in their place (one panel reads better than two
    stacked locked boxes).
- **Attendance buttons** — unchanged; the existing `{% if not current_user %}`
  branch already shows the sign-in CTA. Point it at the same sign-in URL as the
  locked panel.

### Locked panel
- One white card matching the existing `.detail-card` / `.race-selector` surface,
  sitting where the gated sections were.
- Centre a title, body and a primary button styled like `.attendance-btn--going`.
- Draft copy (adjust freely): title `See the full race lineup`; body
  `Distances, climb, prices, cutoffs and registration status for every race at
  this event. Free once you sign in.`; button `Sign in to see race details`. It
  is an invitation, not an error — no apology, no access-denied tone.
- Add a `.locked-panel` class in `main.css` using existing tokens. Responsive to
  mobile; visible keyboard focus on the button.

### Sign-in returns to the event page (in scope)
Without this the gate leaks its own purpose: a visitor who signs in from the
locked panel would land on `/` and lose the event they came for.
- The locked-panel button and the attendance sign-in CTA link to
  `/auth/google?next=<current event path>`.
- `/auth/google` reads `next`, validates it is a local same-site relative path
  (must start with a single `/`; reject absolute URLs and protocol-relative `//`
  to avoid an open redirect), and carries it through the OAuth round trip via the
  `state` value or the session.
- `/auth/google/callback` redirects to the validated `next` on success, falling
  back to `/` when absent or invalid.
- Build the authorize URL with `state` in `GoogleAuthService`; keep validation in
  the route or service, not the template.

### Acceptance criteria
- Anonymous request returns 200 with event name, hero image, location, date and
  the going/interested count.
- View source on the anonymous response contains none of the gated race data:
  no distances, ascent, price, cutoff, registration status or race-detail fields
  anywhere in the HTML.
- Anonymous avatar row shows only grey circles, with the `+N` overflow badge
  preserved past four.
- Signed-in rendering of every element is unchanged from before this phase.
- Signing in from a gated event page returns the user to that same event page; a
  missing or non-local `next` falls back to `/`; absolute or protocol-relative
  values are rejected.

---

## Phase 3 — Participant list (privacy-filtered names)

### Objective
For signed-in viewers, show who is going and who is interested by name, in a
"Who's coming" section in the page body, with each attendee shown or hidden
according to their own privacy tier. For anonymous visitors, this section follows
the phase 2 gate.

### Depends on
The filtered `interested_users` list confirmed in the prerequisites. The service
returns already-filtered identity lists for both going and interested; the
template renders whatever it is given and never evaluates a privacy rule itself.

### Behaviour
- **Signed in:** a "Who's coming" section with two columns, going and interested.
  Each visible attendee is an avatar plus display name. The count always reflects
  the true total; attendees whose identity is hidden from this viewer (private, or
  crews-only with no shared crew) still contribute to the count but are not named.
  Reconcile the difference with a neutral line such as grey circles and
  `and N others`, worded the same whether someone is private or crews-blocked so
  it never leaks which.
- **Anonymous (decided: separate nudge):** render the same "Who's coming" section,
  in the same two-column layout, but with no names. Each column shows grey
  placeholder circles and a light inline text link — `Sign in to see who's going`
  and `Sign in to see who's interested`. Do not add another primary button here:
  the page already has the action-bar sign-in and the locked-panel button, so the
  nudge stays as quiet text links to avoid stacking calls to action. The grey
  circles match the gated avatar row from phase 2. This section is a strict
  addition on top of the phase 2 gate; collapsing it later (folding it into the
  race-data locked panel) is a one-block deletion if it is ever unwanted.

### Worked example (from the privacy spec, for test data)
Going: Alice (private), Bob (crews-only, in crew C), Dan (public), Erin (public).
Interested: Fay (public), Gus (public), Hana (private).
- Anonymous: no names.
- Signed in, no shared crew: Dan and Erin named; Alice and Bob shown as
  `and 2 others`. Interested: Fay and Gus; Hana as `and 1 other`.
- Signed in, in crew C: Bob is now named; Alice stays `and 1 other`.

### Scope
- `app/services/attendance_service.py` — only if the filtered interested list is
  not already returned.
- `app/templates/event.html` — the new "Who's coming" body section.
- `static/css/main.css` — section and row styles, reusing avatar and token
  styles already present.

### Acceptance criteria
- Signed-in viewers see filtered going and interested name lists; counts match
  the earlier worked example across the no-shared-crew and shared-crew cases.
- Hidden attendees still contribute to the count and are never named or hinted at
  individually.
- The template contains no privacy branching beyond `current_user`; all filtering
  comes from the service.
- Anonymous viewers see no names, consistent with the phase 2 gate.