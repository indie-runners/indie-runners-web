# W-087 — Two crew dead-ends still send the reader back to Settings, which no longer lists crews

`priority: 5` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-31 (while on W-078), filed at the W-078 review`

## What is wrong

W-078 moved a user's crews from `/settings` to their profile and pointed
the hub's and the create form's back links at `/profile`. Two crew pages
still read `← Settings`:

`crews_hidden.html:15` (a non-member or a made-up slug on `/crews/{slug}`)
and `crews_invite_invalid.html:15` (a dead invite link):

```html
  <a href="/settings" class="back-link">← Settings</a>
```

Settings no longer has anything about crews, so the link leads away from
the one place a reader could act (create a crew, open one they are in).
Not broken: the page loads. W-078's spec named the crew page only, so the
developer left these and flagged them.

## Acceptance

1. Both read `← My profile` and link to `/profile`, like the hub and the
   create form since 1.9.53.
2. Each rendered once signed in (a slug you are not in; a rotated token).

## Out of scope

- What anon sees on these routes (W-085).
- The pages' copy beyond the back link.
