# W-090 — Every signed-in surface shows a runner's full name from Google

`priority: 1` · `effort: S` · `area: services` · `deploy: immediate`
`source: docs/IDEAS.md 2026-11-01 (Paulo: highest priority)`

**THE NEXT TICKET.** Paulo's word jumps the crews arc. Priority 1 is
normally site-down only; it is used here so the board's ordering says
what Paulo said.

## What is wrong

`web.users.display_name` holds Google's full `name`, written on first
sign-in and overwritten on every later one. Every surface that names a
user reads that column, so each shows first and last name.

## Evidence

Paulo, `docs/IDEAS.md` 2026-11-01:

> at the moment we get the user name from Google, and that means
> first name and last name. It is imperative we show first name and the
> initial of the last name instead.

`app/services/user_service.py`:

```
30:                display_name=userinfo.get("name"),
51:            user.display_name = userinfo.get("name")
```

Readers of the column: `base.html` (nav initial), `event.html` Who's
coming (name and link), `profile.html` (`<title>`, `h1`, avatar `alt`),
`partials/avatar_strip.html` (`alt`), `crew_service.py:164`
(`u.display_name AS user_name`, the hub), `main.py` `/me`.

PM, read-only, 2026-11-01: most users have multi-word names, and not
all of them sign in monthly. So a sign-in-only fix leaves some users on
their full name indefinitely. Existing rows need a backfill.

## Acceptance

1. Sign-in stores `given_name` + space + first letter of `family_name`
   + `.`, e.g. `Paulo M.`. No `family_name` → `given_name` alone. No
   `given_name` → the same rule on `name`'s first and last
   whitespace tokens. One token → as is. Nothing → NULL, which the
   templates already render as `Runner`.
2. One helper does this, called at both write sites (lines 30 and 51).
   It has an assert-based self-check covering the five cases above.
3. `migrations/015_display_name_short.sql` rewrites existing rows by the
   `name` rule: first token, space, first letter of the last token, `.`,
   only where `display_name` has more than one token. **Written by the
   developer, run by Paulo after the code is serving**, never before:
   a sign-in on the old code would write a full name back.
4. Verify locally, signed in: nav, profile (`<title>` and `h1`), an
   event's Who's coming and a crew hub all show the short form. Anon:
   the event page and `/profile/<id>` carry no name, as today.
5. Changelog entry with the full reasoning. ARCHITECTURE § `web.users`
   says what `display_name` holds.

## Out of scope

- **A user-editable display name.** Nobody asked; it is a settings form
  and a validation story.
- **Storing `given_name` / `family_name` as columns.** The short form is
  all any surface shows. Data the product never renders is data it
  should not keep.
- **The 3 rows with three or more name tokens.** The backfill takes the
  last token, which can pick the second surname. The next sign-in
  corrects them from Google's own fields.
- **The privacy page.** It says we *receive* the display name from
  Google, which stays true.
- **Crew names** (`web.crews.display_name`), a different column.

## Decision taken for Paulo (veto at review)

The format is `Paulo M.`, with the period. Say so if it should be
`Paulo M`.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-091** — 2026-11-01, reviewing
`fix/names-first-plus-initial` at `3fc1979`. One helper, both write
sites, five asserts. The session cookie holds only `user_id`, so no
name is cached outside the column. The OAuth scope is
`openid email profile`, so Google sends `given_name` / `family_name`
whenever the account has them. The changelog names the wrong belief,
the cost and the evidence, and it does not claim a render it could not
make. Docs: 39 added lines. W-091 is the PM's own spec gap: a
multi-token `given_name` with no `family_name` keeps the full name.
Format `Paulo M.` stands unless Paulo vetoes it.

**Not verified:** a real Google sign-in through 1.9.56. Nobody can mint
one from a session, so the write path is proved by the asserts and by
reading two one-line substitutions, not by a run. The first production
sign-in after the deploy settles it (routed check 41). Also not
verified: 015 against the live rows. Its expression was previewed on
literals, and the WHERE selected every multi-word row. **Run 015 once**, after
1.9.56 is serving. Its "re-runnable" header is wider than its guard
(W-091).
