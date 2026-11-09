# W-041 — Two crews can share a name; the second is silently suffixed

`priority: 3` · `effort: S` · `area: services` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-23 (Paulo, written from a scraper session)`

## What is wrong

Paulo: *"can crews created by different people have the same name? It
should not be the case!"*

`CrewService.create_crew` (`app/services/crew_service.py:30`, master)
handles a taken slug by retrying `-2` … `-11`. So a second "<Name>"
is created as `/crews/<name>-2`, and every page shows
`display_name`, so the two read the same. The invite screen ("Join
<name>") is where it matters: someone holding a link can't tell which
crew it is.

## Evidence

From `docs/IDEAS.md` (verified 2026-10-23, `web.crews`, counts only):

> One crew name is held by two crews created by two different
> users, identical including case, and the second slug carries a numeric
> suffix.

**No migration is needed.** `migrations/010_crews.sql:24`:

> `slug         VARCHAR(64) NOT NULL UNIQUE,`

and `_slugify` already folds case and surrounding spaces
(`name.strip().lower()`). `create_crew` is the only writer of
`display_name`. Grepping `display_name =` under `app/` finds no rename
path for crews.

## The IDEAS questions, answered (PM)

1. **Unique how?** By slug. Refuse when the base slug is taken, and
   don't suffix.
2. **Same creator too?** One rule for everyone.
3. **The existing pair:** not this ticket. See below.
4. **What the user sees:** `/crews/new` re-renders with "That name is
   taken" and keeps what was typed. `main.py:659-660` already turns a
   `ValueError` from `create_crew` into a form message, so use that path.
5. **The refusal reveals that a crew with that name exists.** Accepted.
   Every uniqueness rule reveals that much, and it exposes a name, not
   members.

## Acceptance

1. Creating a crew whose slug is taken is refused with the message from
   4, and no row is written. Shown on a local DB with two attempts,
   quoted.
2. The unique index is still what decides, not a check before the
   insert. Two concurrent creates must not both succeed. Refusing on the
   `IntegrityError` the loop already catches gives you that.
3. The `-2`…`-11` loop and `_SLUG_MAX_SUFFIX` are gone if nothing else
   uses them.
4. A known side effect is named in the changelog. The suffixed crew
   holds `<name>-2`-style slugs, so a new crew named "<name> 2"
   is refused as taken although no crew displays that name.

## Out of scope

- **Renaming the existing pair.** There is no rename path in the app, so
  this is a production `UPDATE` on `web.crews`. Which crew renames, and
  who tells its members, is Paulo's call, and it runs only with his
  approval. It doesn't block this ticket: the code change stops new
  duplicates and the pair exists either way.
- A rename feature for crews.
- A unique index on `display_name` (the slug already is one).

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-049** — 2026-10-26. The
`IntegrityError` on the `UNIQUE` slug decides, with no pre-check. `slug`
is the only unique constraint on `web.crews` (`created_by` has no FK), so
"That name is taken" is the only thing that error can mean. The loop and
`_SLUG_MAX_SUFFIX` are gone. The changelog names the wrong belief, its
cost, the "<name> 2" side effect, and that concurrency is by
construction. ARCHITECTURE's crews paragraph is updated. Docs: 46 lines.
`deploy: batched`.

**This spec was wrong, amended here.** Acceptance 1 asked for "a local
DB". There is none: `.env` reaches the one Cloud SQL instance. The
developer verified against production in a session that was rolled back:
counts (crews, memberships, invites) were 4,6,6 before and 4,6,6 after.
They refused a padded, re-cased name, and an existing crew's name
uppercased. The route was run with `dev.sh` from the worktree
(`/proc/<pid>/cwd` checked) and a minted cookie. A taken name returned
400 with the error div and the typed value kept. Anon got 401.

W-049 is older than this branch. A first crew named "New" always got slug
`new`, and `/crews/new` shadows its page. W-041 makes the slug stick for
everyone after.

**Not verified:** the route's success path (`303 → /crews/{slug}?created=1`)
after the change. Only the service ran it, with `commit` swapped for
`flush`. The route code is unchanged, so this is accepted. Two concurrent
creates were not run; that rests on the unique index. A 65+ character
name is still a 500 (`DataError`, slug is `VARCHAR(64)`). That is older
than this branch and is in DEV_NOTES for triage. I did not re-run any of
it myself, because that needs a DB session. The production check is
routed check 21.
