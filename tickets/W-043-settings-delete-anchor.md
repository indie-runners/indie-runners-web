# W-043 — Legal pages link to /settings, not to its delete section

`priority: 5` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-23 (developer, while on W-034; kept out of W-034 on Paulo's call)`

## What is wrong

From `docs/IDEAS.md`:

> Terms §9 and privacy §8 both link to plain `/settings`. The delete section
> sits at the bottom, so "Settings → Delete account" means scroll to find it.
> An `id` on that section (`settings.html:98`) and `/settings#delete-account`
> in both links would land the user on it.

## Acceptance

1. The delete section carries `id="delete-account"`. `/terms` §9 and
   `/privacy` §8 link to `/settings#delete-account`.
2. Signed in, clicking either link lands on the section (checked in the
   browser).
3. Signed out, the link still reaches sign-in (W-035's 303). The
   fragment is lost through the Google round trip, so the user lands on
   the top of `/settings`. That is expected; say so in the changelog
   rather than fix it.

## Out of scope

- Carrying the fragment through OAuth.
- The legal text and its revision dates. A link target is not a
  revision.
