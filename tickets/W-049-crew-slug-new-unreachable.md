# W-049 — Two crew names the slug cannot hold: "New" (its page is the create form) and anything over 64 characters (a 500)

`priority: 3` · `effort: S` · `area: services` · `deploy: batched`
`source: W-041 review, 2026-10-26 (PM, read from source); widened in triage 2026-10-26 with docs/DEV_NOTES.md 2026-10-26 (while on W-041)`

## What is wrong

`_slugify("New")` is `new`. `GET /crews/new` (`app/main.py:654`) is
registered before `GET /crews/{slug}` (`:689`), so the crew's URL serves
the create form. After creating it, the creator is redirected to
`/crews/new?created=1` and sees an empty form. The crew has no page, so
its invite URL is never shown to anyone.

**This is older than W-041.** The suffix loop only ran on a collision, so
the first crew named "New" always got `new`. W-041 makes it stick: the
next person to try "New" is now told "That name is taken", where before
they got a working `new-2`.

**Widened in triage: a name over 64 slug characters is a 500.** The
developer's note: "`crews_new.html` allows `maxlength="120"` and
`display_name` is `VARCHAR(120)`, but `slug` is `VARCHAR(64)`
(`010_crews.sql:24`) and `_slugify` does not truncate." Confirmed from
source in triage. `create_crew` catches only `IntegrityError`, and the
route catches only `ValueError` (`main.py:675`), so the `DataError`
reaches the user as a 500. Both are the same fault: `create_crew` never
checks that the slug it computed can be stored and served. Same function,
same form, same `ValueError` path, so this is one ticket. Raised to p3
because the 500 is a broken page.

## Evidence

Read from source, not reproduced. `crew_service.py` has no reserved-slug
check (`grep -n reserved\|\"new\"` finds nothing). `/crews/join` with no
token is not affected: it matches `/crews/{slug}`, not
`/crews/join/{token}`. Whether production already holds a `new` crew is
unknown. The review ran no DB session.

## Acceptance

1. `create_crew` refuses a name whose slug is `new`, with a form message
   (the existing `ValueError` path, as W-041 uses).
2. The check reads one set of reserved slugs, named next to `_slugify`,
   so the next fixed `/crews/<word>` route has an obvious place to go.
3. A name whose slug is over 64 characters gets a form message, not a
   500. Truncating instead is allowed only if two different long names
   cannot then collide and be told "That name is taken". Say which
   approach in the changelog.
4. If production has a crew with slug `new`, that goes to Paulo with
   the count only. Renaming it is a production `UPDATE`, his call.

## Out of scope

- Renaming an existing `new` crew (as above).
- Moving crew pages to a prefix that cannot collide (`/c/{slug}`): it
  breaks every invite URL already shared.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-052** — 2026-10-26. Both checks
sit in `create_crew` before the write, on the existing `ValueError`
path. `_RESERVED_SLUGS` sits next to `_slugify` (acceptance 2). The
length limit is read from the model, which matches `010_crews.sql:24`.
The changelog says why it refuses rather than truncates (acceptance 3)
and names the wrong belief, the cost (no page; a 500) and the evidence.
ARCHITECTURE's crews paragraph is updated. Verified from the worktree's
own uvicorn (`/proc/<pid>/cwd` checked, so not W-009), signed-in with a
minted cookie and anon. Docs: 37 lines. Acceptance 4: count 0, so
nothing goes to Paulo. W-052 is the same fault on `display_name`
(`VARCHAR(120)`, enforced only by the form's `maxlength`). It existed
before this branch and only a direct POST reaches it, so it does not block.

**Not verified:**
- A successful create on this branch. Both checks only raise, above
  code that did not change, so the happy path is unchanged because of
  where they sit, not because anything ran it.
- The exactly-64 boundary (`>` against 64): read from source only. The
  model and the migration agree; nobody looked at the live column.
- That `indie-runners-db` behind the local proxy is the instance Cloud
  Run serves. The developer's 0/0 count holds only for that instance.
  Routed check 23 settles it.
- `docs/TODO.md` ticks "POST … a normal name", but the changelog says no
  successful create was run. If the TODO is right, a test crew was
  written to that database. Ask the developer which one is true.
