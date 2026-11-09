# W-052 — `create_crew` trusts the form's `maxlength`; a crew name over 120 characters is a 500

`priority: 4` · `effort: S` · `area: services` · `deploy: batched`
`source: W-049 review, 2026-10-26 (PM, read from source)`

## What is wrong

`display_name` is `VARCHAR(120)` (`010_crews.sql:25`, `web.py:80`). The
only limit on it is `maxlength="120"` in `crews_new.html:28`, which a
browser enforces and a direct POST does not. `POST /crews/new` takes
`display_name: str = Form(...)` with no length, and `create_crew` checks
only the minimum length and, since W-049, the slug.

A name of 121+ characters whose slug stays short passes every check:
`"a" + "!" * 119 + "b"` slugs to `a-b`. The `INSERT` then raises
`DataError`, which is not a `ValueError`, so it reaches the user as a
500. W-049 fixed this fault for `slug`; `display_name` is the same fault
one column over.

## Evidence

Read from source, not reproduced. A normal browser cannot reach it
(`maxlength`), so it is p4, not p3: a 500 that only a hand-made request
can trigger, with nothing written.

## Acceptance

1. `create_crew` refuses a name longer than the `display_name` column
   with "Crew name is too long" (the W-049 message), read from the
   model the way `_MAX_SLUG_LEN` is.
2. The check runs on the stripped name, which is what is stored.
3. Verified with a direct POST (curl with a minted cookie): 400 and the
   form re-rendered, not 500.

## Out of scope

- Changing the form's `maxlength`: 120 is right for the column. That
  the slug limit (64) can refuse a shorter name is by design (W-049).
- Server-side length checks on other forms. If the developer finds the
  same pattern elsewhere, it goes to `docs/DEV_NOTES.md`.
