# W-042 — Crew members' names don't link to their profiles

`priority: 4` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-23 (Paulo, written from a scraper session)`

## What is wrong

Paulo: *"make peoples profile in listing of members of crews clickable"*.

`app/templates/crews_detail.html:32-48` (master) renders each member's
avatar and `<span class="crew-member-name">` as plain text. The event
page already links attendees to `/profile/{{ u.id }}`
(`event.html:456,476`), so the route and the pattern exist.

## Decisions (PM, answering the IDEAS questions)

1. **`private` members stay plain text.** Their profile shows the hidden
   placeholder to a crew-mate, so a link would lead nowhere. Plain text
   tells them nothing the placeholder wouldn't. `User.visibility` is
   mapped (`app/models/web.py:24`), so the template can branch on it.
2. **The row is one link:** avatar and name together, not the name alone.
3. **You** are linked like anyone else, to your own profile.

## Acceptance

1. On a crew page, a `public` or `crews_only` member's avatar and name
   are one link to `/profile/<id>`, and it returns 200 for a signed-in
   crew-mate. A `private` member's row has no link.
2. Checked locally with at least one member of each visibility, quoted.
   The crew page is signed-in only. Say what a signed-out request gets,
   unchanged.
3. The admin tag and the layout of the row look as before.

## Out of scope

- Changing what a profile shows to whom (`ProfileService._can_view`).
- Member lists anywhere else (settings, invite screen).
