# W-028 — Anonymous attendees render as identical gray "ir" circles

`priority: 4` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-21 (Paulo), "New Indie Runners logo assets", use 3 and Paulo's elaboration (9daa5db). Split from W-024.`

## What is wrong

A signed-out visitor never sees a real attendee: `_is_identity_visible` returns
False for everyone when `viewer_user_id is None`
(`app/services/attendance_service.py:40-41`), so every attendee renders
as `avatar--stock`, a plain circle with the text "ir". A row of them
reads as placeholder, not as people. Signed-in viewers see the same
circle for private and crews-only attendees.

**Paulo's elaboration in IDEAS is the spec** (design, SVG, five
`--anon-bg-*` variables, rules 1-5, steps 1-3, 5). Use it verbatim. This
ticket only adds what it does not say.

## What the spec does not cover

**1. Every render site, found in triage.** Paulo's step 1 says list
them first. Here is the list. Confirm it, do not trust it:

- `partials/avatar_strip.html:17-19`, the stock loop in the macro.
- Its callers: `race_tile.html:25,32` (tile), `:80,87` (hover, `lg`),
  `event.html:507,515` (who's coming).
- **`static/js/attendance.js:21`** builds `avatar--stock` client-side
  after an attendance toggle, with its own hardcoded hex palette. A Jinja
  macro does not reach it. It renders a signed-in viewer's hidden
  attendees, so under point 2 it **must** change too, to the same markup
  and the same position-mod-5 rule. Once it has, nothing emits
  `.avatar--stock` and Paulo's step 2 removes it.

**2. Hidden users change too — Paulo, 2026-10-22.** `avatar--stock` is
also how a **signed-in** viewer sees a private or crews-only attendee.
Paulo's answer: change those as well. **This overrides the
elaboration's "do not change avatars for logged-in visitors" for hidden
attendees only.** Real-user avatars (photo or initial) are unchanged.
So every stock circle becomes an anonymous avatar, in both tiers, and
the macro needs no tier branch. Rule 1 holds in both tiers: a signed-in
viewer must not recognise a hidden attendee by colour either.

**3. "Add a test".** There is no test suite (W-003), and this ticket
does not create one. W-003 says start with `RaceService`. Instead, the
changelog quotes the signed-out HTML of one tile with 5+ attendees and
shows that the classes cycle `--anon-0..4` and that no user id, name or
photo URL is present (`grep` it).

## Acceptance

1. Signed-out: tiles, hover overlay and event page show the anonymous
   avatars, coloured by position mod 5. `+N` unchanged.
2. Signed-in: real-user avatars unchanged; hidden attendees show the
   anonymous avatar, in the server render **and** after a toggle (the JS
   path). Check one with a private attendee.
3. The quoted render check from point 3 above.
4. Palette change is CSS-only: no colour in the macro or the template.
5. Changelog entry.

## Out of scope

- The favicon and the logo pack (W-024). Nothing here needs it.
- `attendance.js`'s hardcoded palette for **real-user initials**
  duplicating `--avatar-color-*`. A real drift, but not the anonymous
  avatars.
- A test harness (W-003).

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-062, W-063** — 2026-10-27.
Reviewed `master...fix/anonymous-avatars` at `07a873c`. All seven checks
pass; docs diff is 58 lines. Verified by the developer on this worktree
(`/proc/<pid>/cwd`, so not W-009's wrong checkout): anon `/` and an anon
event page, including headless Chrome; signed-in `/` and an event page
byte-diffed against master. The macro and `attendance.js` give the same
class sequence on the same input. No user id, name or photo URL in the
anon strip. Acceptance 3's "5+ attendees" was impossible (live max 3, tile
cap 3); the wrap was shown by rendering the macro directly. Accepted.
W-062 and W-063 are the developer's drive-bys, both pre-existing. Ticket
is `deploy: batched`.

Outside this verdict: W-064 (no cache policy on `/static`) and the
TODO carry-forward, now on W-060's row and in a handoff to the chief of
staff. The developer followed `developer.md` step 3.

**Not verified:**
- **A signed-in viewer with a hidden attendee on an upcoming race**, server
  render (acceptance 2). The signed-in byte-diff only shows the unchanged
  path didn't regress: user 15 had no hidden attendees in view, and all 7
  private attendances are on past occurrences.
- **The JS path in a browser.** `buildAvatarHtml` ran in node. Nobody
  clicked Going/Interested on this branch.
- **`--anon-4`**, which no current cap reaches.
- What settles the first two: Paulo sets one test user to private, marks
  an upcoming race with them, then one signed-in page load as another user
  and one toggle.
